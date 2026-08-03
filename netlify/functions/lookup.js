/**
 * Barcode fallback lookup.
 *
 * Runs on Netlify's servers, not in the browser. That matters for two reasons:
 * the upstream APIs send no CORS headers so a web page cannot call them
 * directly, and any paid API key added later stays server-side instead of
 * being readable in the page source.
 *
 * Only called when Open Food Facts has no record, so the free tier's daily
 * quota is spent on genuine misses. Responses are cached at the CDN for a day
 * to stretch that quota further.
 */

const UA = "EcoTrace/1.0 (barcode impact scanner)";

async function fromUPCitemdb(code) {
  const r = await fetch(`https://api.upcitemdb.com/prod/trial/lookup?upc=${encodeURIComponent(code)}`, {
    headers: { "User-Agent": UA }
  });
  if (r.status === 429) return { rateLimited: true };
  if (!r.ok) return null;

  const j = await r.json();
  const it = j && Array.isArray(j.items) && j.items[0];
  if (!it) return null;

  return {
    source: "UPCitemdb",
    name: it.title || "",
    brand: it.brand || it.manufacturer || "",
    category: it.category || "",
    description: it.description || "",
    image: Array.isArray(it.images) && it.images[0] ? it.images[0] : null,
    model: it.model || "",
    weight: it.weight || "",
    currency: it.currency || "",
    priceLow: it.lowest_recorded_price || null,
    priceHigh: it.highest_recorded_price || null
  };
}

export default async (req) => {
  const code = (new URL(req.url).searchParams.get("code") || "").replace(/\D/g, "");

  if (!code || code.length < 6 || code.length > 14) {
    return Response.json({ found: false, reason: "bad-code" }, { status: 400 });
  }

  try {
    const hit = await fromUPCitemdb(code);

    if (hit && hit.rateLimited) {
      return Response.json(
        { found: false, reason: "rate-limited" },
        { status: 200, headers: { "Cache-Control": "public, max-age=300" } }
      );
    }
    if (!hit || !(hit.name || hit.brand)) {
      return Response.json(
        { found: false, reason: "not-in-database", code },
        { status: 200, headers: { "Cache-Control": "public, max-age=3600" } }
      );
    }

    return Response.json(
      { found: true, code, ...hit },
      { status: 200, headers: { "Cache-Control": "public, max-age=86400" } }
    );
  } catch (e) {
    return Response.json({ found: false, reason: "upstream-error" }, { status: 200 });
  }
};

export const config = { path: "/api/lookup" };
