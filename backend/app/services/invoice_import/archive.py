"""Safe extraction helpers for electronic invoice archive packages."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional
import io
import zipfile

from app.config import settings


class UnsafeArchiveError(ValueError):
    """Raised when an uploaded archive is unsafe or structurally invalid."""


@dataclass(frozen=True)
class ExtractedInvoicePackage:
    source_archive_name: str
    package_dir: Path
    xml_path: Path
    pdf_path: Optional[Path]
    ofd_path: Optional[Path]


def _assert_safe_member_name(name: str) -> None:
    path = Path(name)
    if path.is_absolute() or ".." in path.parts:
        raise UnsafeArchiveError(f"Unsafe archive path: {name}")


def _assert_size(info: zipfile.ZipInfo, limit: int) -> None:
    if info.file_size > limit:
        raise UnsafeArchiveError(f"Archive member exceeds configured size limit: {info.filename}")


def _nested_archive_stats(nested_bytes: bytes) -> tuple[int, int]:
    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
        files = [info for info in nested.infolist() if not info.is_dir()]
        return len(files), sum(info.file_size for info in files)


def _extract_nested_invoice(source_archive_name: str, nested_bytes: bytes, target_dir: Path) -> ExtractedInvoicePackage:
    target_dir.mkdir(parents=True, exist_ok=True)
    xml_paths: list[Path] = []
    pdf_path: Optional[Path] = None
    ofd_path: Optional[Path] = None

    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
        members = nested.infolist()
        files = [info for info in members if not info.is_dir()]
        if len(files) > settings.INVOICE_IMPORT_MAX_FILES:
            raise UnsafeArchiveError("Invoice archive contains too many files")
        if sum(info.file_size for info in files) > settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE:
            raise UnsafeArchiveError("Invoice archive expanded size exceeds configured limit")
        for info in members:
            _assert_safe_member_name(info.filename)
            _assert_size(info, settings.INVOICE_IMPORT_MAX_FILE_SIZE)
            if info.is_dir():
                continue
            suffix = Path(info.filename).suffix.lower()
            if suffix == ".zip":
                raise UnsafeArchiveError("Nested invoice archive contains another zip")
            output_path = target_dir / Path(info.filename).name
            output_path.write_bytes(nested.read(info))
            if suffix == ".xml":
                xml_paths.append(output_path)
            elif suffix == ".pdf":
                pdf_path = output_path
            elif suffix == ".ofd":
                ofd_path = output_path

    if len(xml_paths) != 1:
        raise UnsafeArchiveError(f"Invoice archive must contain exactly one XML file: {source_archive_name}")

    return ExtractedInvoicePackage(
        source_archive_name=source_archive_name,
        package_dir=target_dir,
        xml_path=xml_paths[0],
        pdf_path=pdf_path,
        ofd_path=ofd_path,
    )


def extract_invoice_archives(batch_zip: BinaryIO, work_dir: Path) -> list[ExtractedInvoicePackage]:
    packages: list[ExtractedInvoicePackage] = []
    total_expanded_size = 0
    total_nested_files = 0
    with zipfile.ZipFile(batch_zip) as batch:
        members = batch.infolist()
        files = [info for info in members if not info.is_dir()]
        if len(files) > settings.INVOICE_IMPORT_MAX_FILES:
            raise UnsafeArchiveError("Batch archive contains too many files")
        if sum(info.file_size for info in files) > settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE:
            raise UnsafeArchiveError("Batch archive expanded size exceeds configured limit")
        for index, info in enumerate(members, start=1):
            _assert_safe_member_name(info.filename)
            _assert_size(info, settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE)
            if info.is_dir():
                continue
            if Path(info.filename).suffix.lower() != ".zip":
                raise UnsafeArchiveError("Top-level archive may contain invoice zip files only")
            nested_bytes = batch.read(info)
            nested_file_count, nested_expanded_size = _nested_archive_stats(nested_bytes)
            total_nested_files += nested_file_count
            total_expanded_size += nested_expanded_size
            if total_nested_files > settings.INVOICE_IMPORT_MAX_FILES:
                raise UnsafeArchiveError("Batch recursive file count exceeds configured limit")
            if total_expanded_size > settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE:
                raise UnsafeArchiveError("Batch recursive expanded size exceeds configured limit")
            package_dir = work_dir / f"invoice_{index:04d}"
            packages.append(_extract_nested_invoice(info.filename, nested_bytes, package_dir))
    return packages
