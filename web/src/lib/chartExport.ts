/**
 * Chart Export Utilities
 * Export Vedic charts (North / South Indian) to clean SVG or 2x high-resolution PNG.
 */

export function exportSvgToFile(svgElement: SVGSVGElement, filename: string): void {
  const serializer = new XMLSerializer();
  const source = serializer.serializeToString(svgElement);
  const blob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename.endsWith(".svg") ? filename : `${filename}.svg`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function exportPngToFile(
  svgElement: SVGSVGElement,
  filename: string,
  scale = 2
): Promise<void> {
  return new Promise((resolve, reject) => {
    try {
      const serializer = new XMLSerializer();
      let source = serializer.serializeToString(svgElement);

      // Ensure xmlns is present for standalone rendering
      if (!source.match(/^<svg[^>]+xmlns="http:\/\/www\.w3\.org\/2000\/svg"/)) {
        source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
      }

      const svgBlob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
      const url = URL.createObjectURL(svgBlob);
      const img = new Image();

      img.onload = () => {
        try {
          const width = (svgElement.clientWidth || 520) * scale;
          const height = (svgElement.clientHeight || 520) * scale;

          const canvas = document.createElement("canvas");
          canvas.width = width;
          canvas.height = height;

          const ctx = canvas.getContext("2d");
          if (!ctx) {
            URL.revokeObjectURL(url);
            reject(new Error("Canvas 2D context not available"));
            return;
          }

          // Solid background fill matching app dark surface
          ctx.fillStyle = "#0c1222";
          ctx.fillRect(0, 0, width, height);

          // Draw SVG scaled onto canvas
          ctx.drawImage(img, 0, 0, width, height);

          canvas.toBlob((blob) => {
            URL.revokeObjectURL(url);
            if (blob) {
              const pngUrl = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = pngUrl;
              a.download = filename.endsWith(".png") ? filename : `${filename}.png`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
              URL.revokeObjectURL(pngUrl);
              resolve();
            } else {
              reject(new Error("Failed to create PNG blob"));
            }
          }, "image/png");
        } catch (err) {
          URL.revokeObjectURL(url);
          reject(err);
        }
      };

      img.onerror = (err) => {
        URL.revokeObjectURL(url);
        reject(err);
      };

      img.src = url;
    } catch (err) {
      reject(err);
    }
  });
}
