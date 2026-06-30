export async function onRequestGet(context) {
  const url = new URL(context.request.url);
  const path = url.searchParams.get("path") || "/cinema/perugia/";
  const mode = url.searchParams.get("mode") || "parsed";
  const origin = "https://ucicinemas.it";
  const targetUrl = `${origin}${path}`;

  const allowedPaths = ["/cinema/", "/film/", "/_nuxt/"];
  if (!allowedPaths.some((p) => path.startsWith(p))) {
    return new Response(JSON.stringify({ error: "Path not allowed" }), {
      status: 403,
      headers: { "Content-Type": "application/json" },
    });
  }

  try {
    const upstreamResp = await fetch(targetUrl, {
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
      },
      redirect: "follow",
    });

    const html = await upstreamResp.text();

    if (mode === "raw") {
      return new Response(html, {
        status: upstreamResp.status,
        headers: {
          "Content-Type": "text/html; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
        },
      });
    }

    const parsed = extractShowtimeData(html, path);
    return new Response(JSON.stringify(parsed, null, 2), {
      status: 200,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({ error: err.message, path }),
      { status: 502, headers: { "Content-Type": "application/json" } }
    );
  }
}

function extractShowtimeData(html, path) {
  const result = {
    source: path,
    html_length: html.length,
    framework: null,
    webticToken: null,
    apikey: null,
    showtimes: [],
  };

  const isCloudflareBlock =
    html.includes("Attention Required") || html.includes("you have been blocked");
  if (isCloudflareBlock) {
    result.error = "Cloudflare block";
    return result;
  }

  if (html.includes("__NUXT__")) {
    result.framework = "nuxt";
    const nuxtMatch = html.match(/window\.__NUXT__\s*=\s*([\s\S]*?)<\/script>/);
    if (nuxtMatch) {
      try {
        const nuxtStr = nuxtMatch[1].trim().replace(/;$/, "");
        const nuxtData = new Function("return " + nuxtStr)();

        // Look for webtic token in nested config
        const findToken = (obj, depth = 0) => {
          if (depth > 5 || !obj || typeof obj !== "object") return;
          for (const [k, v] of Object.entries(obj)) {
            if (/webtic|apikey|api.key/i.test(k) && typeof v === "string" && v.length > 5) {
              result.webticToken = result.webticToken || v;
              result.apikey = result.apikey || v;
            }
            if (typeof v === "object") findToken(v, depth + 1);
          }
        };
        findToken(nuxtData);

        // Look for showtimes/sessions in Nuxt data
        const findShowtimes = (obj, depth = 0) => {
          if (depth > 6 || !obj || typeof obj !== "object") return;
          if (Array.isArray(obj)) {
            for (const item of obj) findShowtimes(item, depth + 1);
            return;
          }
          // Check if this object looks like a movie with showtimes
          if (obj.title && (obj.sessions || obj.showings || obj.showtimes)) {
            const sessions = obj.sessions || obj.showings || obj.showtimes;
            if (Array.isArray(sessions) && sessions.length > 0) {
              result.showtimes.push({
                title: obj.title,
                slug: obj.slug || null,
                sessions: sessions.map((s) => ({
                  time: s.startTime || s.time || null,
                  screen: s.screenName || s.screen?.name || null,
                  language: s.language?.name || s.language || null,
                })),
              });
            }
          }
          for (const v of Object.values(obj)) findShowtimes(v, depth + 1);
        };
        findShowtimes(nuxtData);
      } catch (e) {
        result.nuxt_parse_error = e.message;
      }
    }
  } else if (html.includes("data-astro")) {
    result.framework = "astro";
  }

  // Fallback: regex for webticToken
  if (!result.webticToken) {
    const m = html.match(/webticToken['":\s]+['"]([\w\-]+)['"]/);
    if (m) result.webticToken = m[1];
  }

  return result;
}
