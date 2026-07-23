import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";

const source = readFileSync(
  path.resolve(process.cwd(), "src/views/system/SystemSettings.vue"),
  "utf-8",
);

describe("SystemSettings MinerU workflow", () => {
  it("provides separate save and test-and-enable actions", () => {
    expect(source).toContain(">保存配置</el-button>");
    expect(source).toContain(">测试连接并启用</el-button>");
    expect(source).toContain("async function persistMineruConfig");
    expect(source).toContain("mineru_enabled: false");
    expect(source).toContain("/system/config/mineru/test");
    expect(source).toContain("await systemStore.fetchAdminConfig()");
  });

  it("validates HTTPS and a configured API key before saving", () => {
    expect(source).toContain("new URL(url).protocol !== 'https:'");
    expect(source).toContain("mineru_api_key_configured");
    expect(source).toContain("MinerU API Key");
  });
});
