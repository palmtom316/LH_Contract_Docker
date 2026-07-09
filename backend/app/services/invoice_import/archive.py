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


def _extract_nested_invoice(source_archive_name: str, nested_bytes: bytes, target_dir: Path) -> ExtractedInvoicePackage:
    target_dir.mkdir(parents=True, exist_ok=True)
    xml_paths: list[Path] = []
    pdf_path: Optional[Path] = None
    ofd_path: Optional[Path] = None

    with zipfile.ZipFile(io.BytesIO(nested_bytes)) as nested:
        for info in nested.infolist():
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
    with zipfile.ZipFile(batch_zip) as batch:
        for index, info in enumerate(batch.infolist(), start=1):
            _assert_safe_member_name(info.filename)
            _assert_size(info, settings.INVOICE_IMPORT_MAX_ARCHIVE_SIZE)
            if info.is_dir():
                continue
            if Path(info.filename).suffix.lower() != ".zip":
                raise UnsafeArchiveError("Top-level archive may contain invoice zip files only")
            nested_bytes = batch.read(info)
            package_dir = work_dir / f"invoice_{index:04d}"
            packages.append(_extract_nested_invoice(info.filename, nested_bytes, package_dir))
    return packages
