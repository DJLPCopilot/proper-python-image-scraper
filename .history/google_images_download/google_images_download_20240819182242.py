from bs4 import BeautifulSoup
import os
import time
import requests

class googleimagesdownload:
    
    def __init__(self):
        self.image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif"]

    def download_page(self, query):
        search_url = f"https://www.google.com/search?q={query}&tbm=isch"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"}
        try:
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()  # Ensure the request was successful
            return response.text
        except requests.RequestException as e:
            print(f"Failed to download page: {search_url}, Error: {e}")
            return ""

    def create_directories(self, main_directory, dir_name, thumbnail, thumbnail_only):
        path = os.path.join(main_directory, dir_name)
        if not os.path.exists(path):
            os.makedirs(path)
        if thumbnail or thumbnail_only:
            os.makedirs(os.path.join(path, "thumbnails"))
        return path

    def download_image(self, img_url, main_directory, dir_name, count, prefix, save_source, no_numbering):
        retries = 3
        for attempt in range(retries):
            try:
                response = requests.get(img_url, stream=True)
                response.raise_for_status()
                img_data = response.content
                img_name = os.path.basename(img_url)
                img_extension = os.path.splitext(img_name)[1]

                if not img_extension.lower() in self.image_extensions:
                    print(f"Invalid or missing image format for {img_url}. Skipping...")
                    return "", ""

                if prefix:
                    prefix = prefix + "_"
                else:
                    prefix = ""

                if no_numbering:
                    path = os.path.join(main_directory, dir_name, prefix + img_name)
                else:
                    path = os.path.join(main_directory, dir_name, f"{prefix}{count}{img_extension}")

                with open(path, "wb") as img_file:
                    img_file.write(img_data)

                if save_source:
                    list_path = os.path.join(main_directory, f"{save_source}.txt")
                    with open(list_path, "a") as list_file:
                        list_file.write(f"{path}\t{img_url}\n")

                absolute_path = os.path.abspath(path)
                return "success", absolute_path
            
            except requests.RequestException as e:
                print(f"Attempt {attempt + 1} failed for image: {img_url}. Error: {e}")
                time.sleep(1)  # Wait a bit before retrying

        print(f"All attempts failed for image: {img_url}. Skipping...")
        return "fail", ""

    def _get_all_items(self, raw_html, main_directory, dir_name, limit, arguments):
        # Use BeautifulSoup to parse the HTML and extract image URLs
        soup = BeautifulSoup(raw_html, 'html.parser')
        image_elements = soup.find_all('img')

        image_urls = []
        for img in image_elements:
            img_url = img.get('src')
            if img_url and img_url.startswith('http'):
                image_urls.append(img_url)

        print(f"Found {len(image_urls)} images for '{dir_name}'")
        if not image_urls:
            print(f"No images found for {dir_name}. Skipping...")
            return [], 0
        
        count = 0
        for img_url in image_urls:
            if count >= limit:
                break

            print(f"Downloading image {count + 1} from {img_url}")
            status, abs_path = self.download_image(img_url, main_directory, dir_name, count + 1, 
                                                   arguments.get("prefix"), arguments.get("save_source"), arguments.get("no_numbering"))
            if status == "fail":
                print(f"Failed to download image {img_url}. Continuing with the next one...")
            count += 1

        return [img_url for img_url in image_urls], count

    def download(self, arguments):
        search_terms = arguments["keywords"].split(',')
        main_directory = arguments.get("output_directory", "downloads")
        limit = arguments.get("limit", 100)
        
        all_paths = []
        total_errors = 0
        error_log = []
        for search_term in search_terms:
            dir_name = search_term.strip().replace(" ", "_")
            print(f"Now Downloading - {search_term}")
            raw_html = self.download_page(search_term)
            self.create_directories(main_directory, dir_name, arguments.get('thumbnail'), arguments.get('thumbnail_only'))
            paths, errors = self._get_all_items(raw_html, main_directory, dir_name, limit, arguments)
            total_errors += errors
            all_paths.extend(paths)
            if errors > 0:
                error_log.append(f"Failed to download {errors} images for search term: {search_term}")

        # Log errors to a file
        if error_log:
            with open(os.path.join(main_directory, "error_log.txt"), "w") as log_file:
                log_file.write("\n".join(error_log))

        return all_paths, total_errors

def main():
    records = [
        {
            "keywords": "space hopper ball, space hopper animal, space hopper ball with person, space hopper animal with person, space hopper ball without person, space hopper animal without person",
            "limit": 5,
            "output_directory": "space_hopper_images",
            "prefix": "sh",
            "no_numbering": False,
            "save_source": "image_sources",
            "thumbnail": False,
            "thumbnail_only": False,
            "silent_mode": False
        }
    ]
    total_errors = 0
    t0 = time.time()
    
    for arguments in records:
        response = googleimagesdownload()
        paths, errors = response.download(arguments)
        total_errors += errors
    
    t1 = time.time()
    total_time = t1 - t0
    print("\nEverything downloaded!")
    print(f"Total errors: {total_errors}")
    print(f"Total time taken: {total_time} Seconds")

if __name__ == "__main__":
    main()