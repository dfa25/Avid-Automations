// Deploy at script.google.com as a Web App — do NOT run in CI.
// Project → Settings → Script Properties → add SLACK_BOT_TOKEN.
// Deploy settings: Execute as = Me, Who has access = Anyone.
// Copy the Web App URL into Zapier's Webhooks → POST steps (Paths A–I in Zap 2).

/**
 * Receives a POST from Zapier, fetches the file from Slack's private URL,
 * and saves it to the specified Google Drive folder.
 *
 * Expected JSON payload:
 *   fileUrl    — Slack private download URL (requires bot token auth)
 *   folderId   — Google Drive folder ID
 *   fileName   — filename without extension
 *   fileType   — extension without leading dot, e.g. "mp4"
 *   originalTs — Slack message timestamp of the user's original upload
 *   channelId  — Slack channel ID (for adding ✅ reaction via Slack API)
 */
function doPost(e) {
  try {
    var payload    = JSON.parse(e.postData.contents);
    var fileUrl    = payload.fileUrl;
    var folderId   = payload.folderId;
    var fileName   = payload.fileName;
    var fileType   = payload.fileType;
    var originalTs = payload.originalTs;
    var channelId  = payload.channelId;

    if (!fileUrl || !folderId || !fileName || !fileType) {
      return jsonResponse({ status: "error", message: "Missing required field: fileUrl, folderId, fileName, or fileType" });
    }

    var token = PropertiesService.getScriptProperties().getProperty("SLACK_BOT_TOKEN");
    if (!token) {
      return jsonResponse({ status: "error", message: "SLACK_BOT_TOKEN not set in Script Properties" });
    }

    // Fetch file from Slack — private URLs require the bot token.
    // UrlFetchApp streams the response, bypassing Zapier's 250 MB cap.
    var fetchResponse = UrlFetchApp.fetch(fileUrl, {
      headers: { Authorization: "Bearer " + token },
      muteHttpExceptions: true
    });

    if (fetchResponse.getResponseCode() !== 200) {
      return jsonResponse({
        status: "error",
        message: "Slack fetch failed with HTTP " + fetchResponse.getResponseCode()
      });
    }

    var blob   = fetchResponse.getBlob().setName(fileName + "." + fileType);
    var folder = DriveApp.getFolderById(folderId);
    var file   = folder.createFile(blob);

    // Add ✅ reaction to the user's original upload message if timestamps provided.
    if (originalTs && channelId) {
      addSlackReaction(token, channelId, originalTs, "white_check_mark");
    }

    return jsonResponse({ status: "ok", fileId: file.getId(), fileName: file.getName() });

  } catch (err) {
    return jsonResponse({ status: "error", message: err.toString() });
  }
}

/**
 * Adds a Slack emoji reaction to a message.
 * Called on success so the uploader knows their file was routed.
 */
function addSlackReaction(token, channelId, timestamp, emoji) {
  UrlFetchApp.fetch("https://slack.com/api/reactions.add", {
    method: "post",
    contentType: "application/json; charset=utf-8",
    headers: { Authorization: "Bearer " + token },
    payload: JSON.stringify({ channel: channelId, timestamp: timestamp, name: emoji }),
    muteHttpExceptions: true
  });
}

function jsonResponse(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
