export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.searchParams.get("path") || "/cinema/perugia/";
    const mode = url.searchParams.get("mode") || "parsed";
    const origin = env.ORIGIN || "https://ucicinemas.it";
    const targetUrl = `${origin}${path}`;

    const allowedOrigins = ["ucicinemas.it"];
    const targetHost = new URL(targetUrl).hostname;
    if (!allowedOrigins.some((o) => targetHost === o || targetHost.endsWith(`.${o}`))) {
      return new Response(JSON.stringify({ error: "Domain not allowed" }), {
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
          "Accept-Encoding": "gzip, deflate, br",
          "Cache-Control": "no-cache",
          Pragma: "no-cache",
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
            "X-Proxy-Status": upstreamResp.status.toString(),
          },
        });
      }

      const parsed = extractShowtimeData(html, path);
      return new Response(JSON.stringify(parsed, null, 2), {
        status: 200,
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*",
          "X-Proxy-Status": upstreamResp.status.toString(),
          "X-HTML-Length": html.length.toString(),
        },
      });
    } catch (err) {
      return new Response(
        JSON.stringify({ error: err.message, path }),
        { status: 502, headers: { "Content-Type": "application/json" } }
      );
    }
  },
};

function extractShowtimeData(html, path) {
  const result = {
    source: path,
    html_length: html.length,
    framework: null,
    webticToken: null,
    apikey: null,
    cinemas: [],
    showtimes: [],
  };

  const isCloudflareBlock =
    html.includes("Attention Required") ||
    html.includes("you have been blocked") ||
    html.includes("cf-error-details");
  if (isCloudflareBlock) {
    result.error = "Cloudflare block received even from Worker";
    return result;
  }

  if (html.includes("__NUXT__")) {
    result.framework = "nuxt";
    const nuxtMatch = html.match(
      /window\.__NUXT__\s*=\s*([\s\S]*?)<\/script>/
    );
    if (nuxtMatch) {
      result.nuxt_data_length = nuxtMatch[1].length;
      try {
        const nuxtStr = nuxtMatch[1].trim().replace(/;$/, "");
        const nuxtData = new Function("return " + nuxtStr)();
        result.nuxt_keys = Object.keys(nuxtData);

        const config = nuxtData?.data?.config || nuxtData?.config || {};
        if (config.webticToken) result.webticToken = config.webticToken;
        if (config.apikey) result.apikey = config.apikey;
        if (config.webticApikey) result.apikey = config.webticApikey;

        const cinemaData =
          nuxtData?.data?.cinema || nuxtData?.data?.page?.cinema || null;
        if (cinemaData) {
          result.cinema = {
            name: cinemaData.name,
            id: cinemaData.id,
            slug: cinemaData.slug,
          };
        }

        const movies =
          nuxtData?.data?.movies ||
          nuxtData?.data?.page?.movies ||
          nuxtData?.data?.films ||
          [];
        if (Array.isArray(movies)) {
          for (const movie of movies) {
            const showings = extractMovieShowtimes(movie);
            if (showings.length > 0) {
              result.showtimes.push({
                title: movie.title || movie.filmTitle || null,
                slug: movie.slug || null,
                sessions: showings,
              });
            }
          }
        }
      } catch (e) {
        result.nuxt_parse_error = e.message;
      }
    }
  } else if (html.includes("data-astro")) {
    result.framework = "astro";
  }

  const tokenMatch = html.match(
    /webticToken['":\s]+(['"]([\w\-]+)['"])/
  );
  if (tokenMatch) result.webticToken = tokenMatch[2];

  const apiKeyMatch = html.match(
    /(?:apikey|api_key|api-key)['":\s]+(['"]([\w\-]+)['"])/
  );
  if (apiKeyMatch) result.apikey = apiKeyMatch[2];

  if (result.showtimes.length === 0) {
    const scheduleBlocks = html.match(
      /data-showtime[^>]*>[\s\S]*?<\/[^>]+>/gi
    );
    if (scheduleBlocks && scheduleBlocks.length > 0) {
      result.raw_showtime_elements = scheduleBlocks.length;
    }
  }

  return result;
}

function extractMovieShowtimes(movie) {
  const sessions = [];
  const variants = movie.variants || movie.showingGroups || [];

  if (Array.isArray(variants)) {
    for (const variant of variants) {
      const times = [];
      const sessionsList = variant.sessions || variant.showtimes || [];
      for (const session of sessionsList) {
        if (session.startTime) {
          times.push(session.startTime);
        } else if (session.time) {
          times.push(session.time);
        }
      }
      if (times.length > 0) {
        sessions.push({
          language: variant.language?.name || variant.language || null,
          screen: variant.screen?.name || variant.screenName || variant.screen || null,
          attributes: (variant.properties || variant.attributes || []).map(
            (p) => (typeof p === "string" ? p : p.name)
          ),
          times: times.sort(),
        });
      }
    }
  }

  if (sessions.length === 0 && movie.sessions) {
    for (const session of movie.sessions) {
      sessions.push({
        time: session.startTime || session.time,
        screen: session.screenName || session.screen?.name || null,
        language: session.language || null,
      });
    }
  }

  return sessions;
}
