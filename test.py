import os
import time
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration:
# Make sure you have a .env file with LEONARDO_API_KEY set:
# LEONARDO_API_KEY=your_real_api_key_here
API_KEY = os.getenv("LEONARDO_API_KEY")
if not API_KEY:
    raise RuntimeError("Please set the LEONARDO_API_KEY environment variable in your .env file.")

# Base URL for Leonardo.ai API
BASE_URL = "https://api.leonardo.ai"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}


def generate_anime_image(prompt: str,
                         model: str = "leonardo-anime-xl",
                         width: int = 1024,
                         height: int = 1024,
                         steps: int = 30,
                         cfg_scale: float = 7.5) -> str:
    """
    Generate a single anime-style image using Leonardo.ai Text-to-Image endpoint.
    Returns the image generation job ID.
    """
    payload = {
        "model": model,
        "prompt": prompt,
        "width": width,
        "height": height,
        "num_inference_steps": steps,
        "cfg_scale": cfg_scale,
        "samples": 1
    }
    resp = requests.post(f"{BASE_URL}/v1/images/generations", headers=HEADERS, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id")


def wait_for_completion(job_id: str,
                        endpoint: str,
                        interval: int = 5,
                        timeout: int = 300) -> dict:
    """
    Poll the status endpoint until the job is completed or timeout (seconds) is reached.
    """
    elapsed = 0
    while elapsed < timeout:
        r = requests.get(f"{BASE_URL}{endpoint}/{job_id}", headers=HEADERS)
        r.raise_for_status()
        json_data = r.json()
        status = json_data.get("status")
        if status == "succeeded":
            return json_data
        if status == "failed":
            raise RuntimeError(f"Job {job_id} failed")
        time.sleep(interval)
        elapsed += interval
    raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")


def download_asset(asset_url: str, output_path: str):
    """
    Download an asset (image or video) from a URL to a local file.
    """
    r = requests.get(asset_url)
    r.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(r.content)
    print(f"Downloaded asset to {output_path}")


def generate_motion_video(image_url: str,
                          direction: str = "zoom_in",
                          duration: int = 30,
                          strength: float = 0.6,
                          smoothness: float = 0.6) -> str:
    """
    Generate a video clip from a still image using Leonardo.ai Motion generator.
    Returns the motion job ID.
    """
    payload = {
        "image_url": image_url,
        "motion_type": direction,
        "duration_seconds": duration,
        "strength": strength,
        "smoothness": smoothness
    }
    resp = requests.post(f"{BASE_URL}/v1/videos/motion-generations", headers=HEADERS, json=payload)
    resp.raise_for_status()
    data = resp.json()
    return data.get("id")


def main():
    prompt_file = "prompt.txt"
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Prompt file '{prompt_file}' not found.")

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    # 1. Generate anime image
    print("Starting image generation...")
    img_job_id = generate_anime_image(prompt)
    img_job = wait_for_completion(img_job_id, "/v1/images/generations")
    image_url = img_job.get("result", [{}])[0].get("url")
    if not image_url:
        raise RuntimeError("Failed to retrieve generated image URL.")

    image_path = "generated_anime.png"
    download_asset(image_url, image_path)

    # 2. Generate motion video from the generated image
    print("Starting motion video generation (30s)...")
    vid_job_id = generate_motion_video(image_url, direction="pan_left", duration=30)
    vid_job = wait_for_completion(vid_job_id, "/v1/videos/motion-generations")
    video_url = vid_job.get("result", [{}])[0].get("url")
    if not video_url:
        raise RuntimeError("Failed to retrieve generated video URL.")

    video_path = "anime_motion_video.mp4"
    download_asset(video_url, video_path)

    # 3. Cleanup temporary image
    try:
        os.remove(image_path)
        print(f"Removed temporary image file: {image_path}")
    except OSError as e:
        print(f"Could not remove image file: {e}")

    print(f"Video ready! File saved at: {video_path}")


if __name__ == "__main__":
    main()
