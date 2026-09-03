DEPLOYED AND VERIFIED — production readback passed 2026-09-03 11:40 KST on Cloud Run revision bidpilot-demo-00012-vvg (100% traffic, min-instances 1); main = c78c40c

# Cold start versus warm load (live public app, main build, 2026-09-03 KST)

Method: the public URL was left untouched for 18 minutes, then loaded from a fresh signed-out Playwright context at 1440×900. `content_ready` is the time from navigation until the page's headline text is visible. Raw numbers are in `cold-start-results.json`; the earlier warm series (n=3 per route) is in `browser-results.json`.

| Load | DOM loaded | Content ready | What the wait was |
|---|---|---|---|
| Dashboard, first touch after 18 min idle (11:20:24 KST) | 9.0 s | 17.4 s | Cloud Run instance start (≈9 s before any HTML), then Streamlit boot and websocket handshake (≈8 s). No Snowflake is involved on the dashboard. |
| Replay, immediately after, same instance | 1.0 s | 10.8 s | Instance already warm; first `BIDPILOT_READER` JWT connection, run listing and run detail queries (two connections, then cached by `st.cache_data`). |
| Dashboard, warm (2 runs) | 0.9–1.6 s | 2.8–3.5 s | Streamlit rerun only. |
| Replay, warm (2 runs) | 0.8–1.2 s | 2.7–2.8 s | Cached reader results. |
| Local container `docker run` → HTTP 200 | 1.6 s | 3.4 s to dashboard | Streamlit boot alone, without Cloud Run scheduling. |

Reading:

- The ≈20 s skeleton observed earlier is a Cloud Run cold instance plus Streamlit boot. It is not Snowflake latency and not a font wait. The blank Streamlit skeleton cannot be replaced by app code because the app has not started yet.
- The replay adds ≈8 s on its first open per instance for the Snowflake reader. The candidate build names that step on screen (`Connecting to Snowflake` / `Reading the selected run` through `BIDPILOT_READER`) so the wait is legible; the data path itself is unchanged.
- The dashboard and the replay do not share a connection; the dashboard never opens one, so opening the dashboard first is free and only the replay pays the reader connection.
- Connection failure in the container shows `Snowflake could not be reached` with a working `Retry the connection` button at 3.1 s and no fixture text (`candidate-container-replay-connection-error-1440x900.png`).

Stage recommendation, subject to Sergio's approval because it is a Cloud Run setting: keep one instance warm for the finale window with `--min-instances 1`, or have the presenter open the dashboard and then the replay once, at least two minutes before walking on stage, and keep that tab.
