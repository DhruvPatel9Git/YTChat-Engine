import os
import time
import json
from typing import Optional

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from handlers import handle_score, handle_chain, handle_chroma

SCOPES = ["https://www.googleapis.com/auth/youtube.readonly"]


def get_authenticated_service(client_secrets_file: str = "client_secrets.json"):
    flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
    creds = flow.run_local_server(port=0)
    return build("youtube", "v3", credentials=creds)


def get_live_chat_id(youtube, video_id: str) -> Optional[str]:
    resp = youtube.videos().list(part="liveStreamingDetails", id=video_id).execute()
    items = resp.get("items", [])
    if not items:
        print("No video found for id", video_id)
        return None
    details = items[0].get("liveStreamingDetails", {})
    return details.get("activeLiveChatId")


def poll_live_chat(youtube, live_chat_id: str, max_iterations: int = 0):
    """Poll YouTube live chat messages and invoke handlers.

    If `max_iterations` > 0, run that many poll cycles then exit (useful for testing).
    """
    page_token = None
    history = []
    iterations = 0

    while True:
        if max_iterations and iterations >= max_iterations:
            break

        resp = youtube.liveChatMessages().list(
            liveChatId=live_chat_id,
            part="snippet,authorDetails",
            pageToken=page_token,
            maxResults=200,
        ).execute()

        items = resp.get("items", [])
        for it in items:
            snippet = it.get("snippet", {})
            author = it.get("authorDetails", {})
            message_text = snippet.get("displayMessage") or snippet.get("textMessageDetails", {}).get("messageText")
            message = {
                "id": it.get("id"),
                "text": message_text,
                "author": {"name": author.get("displayName"), "channelId": author.get("channelId")},
                "time": snippet.get("publishedAt"),
            }

            score = handle_score(message)
            history = handle_chain(message, history)
            handle_chroma(message)

            # Simple output for now
            print(f"[{message['time']}] {message['author']['name']}: {message['text']} -- score={score.get('score')}")

        page_token = resp.get("nextPageToken")
        wait_ms = resp.get("pollingIntervalMillis", 2000)
        time.sleep(max(0.1, wait_ms / 1000.0))
        iterations += 1


def main():
    youtube = get_authenticated_service()
    video_id = input("Enter YouTube live video ID: ").strip()
    live_chat_id = get_live_chat_id(youtube, video_id)
    if not live_chat_id:
        print("Could not find an active live chat for this video.")
        return

    print("Starting live chat poll (Ctrl-C to stop)...")
    try:
        poll_live_chat(youtube, live_chat_id)
    except KeyboardInterrupt:
        print("Stopped by user")


if __name__ == "__main__":
    main()
