// 保存済みの画像を照合し、同じ文書の中で SVG または PNG を表示する。
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join } from "node:path";

export const imageFormats = ["svg", "png"];
const colors = ["light", "dark"];
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");

export function loadStaticImageFixture(root) {
  const manifestPath = join(root, "manifest.json");
  const pagePath = join(root, "page.html");
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
  const files = [manifestPath, pagePath, join(root, "images.css")];
  assert.equal(manifest.format, 1);
  for (const color of colors) {
    assert.equal(manifest.images[color].length, manifest.count);
    for (const [index, row] of manifest.images[color].entries()) {
      assert.equal(row.index, index);
      assert.ok([row.width, row.height].every((n) => Number.isInteger(n) && n > 0));
      for (const type of imageFormats) {
        const asset = row[type];
        assert.equal(asset.path, color + "/" + index + "." + type);
        const path = join(root, asset.path);
        const bytes = readFileSync(path);
        assert.equal(bytes.length, asset.bytes);
        assert.equal(digest(bytes), asset.sha256);
        files.push(path);
      }
    }
  }
  return { manifest, pagePath, files };
}

export async function showStaticImages(page, images, type, color) {
  return page.evaluate(async ({ images, type, color }) => {
    const start = performance.now();
    document.documentElement.dataset.theme = color;
    const elements = images.map((row) => {
      const img = document.createElement("img");
      img.className = "fig-img";
      img.alt = "図 " + row.index;
      img.width = row.width;
      img.height = row.height;
      img.src = row[type].path;
      return img;
    });
    document.querySelector("main").replaceChildren(...elements);
    const first = elements[0].decode().then(() => performance.now() - start);
    const [, firstDecodeMs] = await Promise.all([Promise.all(elements.slice(1).map((img) => img.decode())), first]);
    const decodeMs = performance.now() - start;
    for (const [index, img] of elements.entries()) {
      const row = images[index];
      if (img.naturalWidth !== row.width || img.naturalHeight !== row.height ||
          img.width !== row.width || img.height !== row.height ||
          img.currentSrc !== new URL(row[type].path, location.href).href) throw new Error("画像または寸法が一致しない");
    }
    return { firstDecodeMs, decodeMs, images: elements.length, documentId: window.__documentId };
  }, { images, type, color });
}
