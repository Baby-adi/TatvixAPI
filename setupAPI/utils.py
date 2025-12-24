from concurrent.futures import ThreadPoolExecutor
import fitz
from PIL import Image
from io import BytesIO
from setupAPI.models import PDFImage, ExtractedText
import pytesseract
from typing import List
import re,requests,uuid
import weaviate.classes.config as wc
from weaviate import WeaviateClient
from tqdm import tqdm
from datetime import datetime, timedelta, timezone

class Utils():
    @staticmethod
    def _process_page(i: int, img: Image, filename: str) -> str:
        """ Method to insert read bytes from file data into mongoDB data-store and implementing OCR to save pdf text into mongoDB data-store """
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format="PNG")

        print(f"[DEBUG] Saving page {i} to MongoDB...")
        pdf_img = PDFImage(filename=f"{filename}_{i}.png")
        pdf_img.file.put(img_byte_arr.getvalue(), content_type="image/png")
        pdf_img.save()

        image_data = img_byte_arr.getvalue()
        img_pil = Image.open(BytesIO(image_data))

        print(f"[DEBUG] Extracting text from page {i}...")
        extracted_text = pytesseract.image_to_string(img_pil)

        text_entry = ExtractedText(image=pdf_img, text=extracted_text)
        text_entry.save()

        return str(pdf_img.id)

    @staticmethod
    def _is_noisy(text):
        # Check if too many repetitive tokens or length is too short
        return (
            text.count("[DATE]") > 3 or
            re.fullmatch(r"[\[\]/A-Z ]{10,}", text.strip()) or
            len(text.strip()) < 5
        )

    @staticmethod
    def _clean_tags(text):
        # Remove citation tags like [DATE], [/DATE], [LAW], [/LAW]
        return re.sub(r"\[/?(DATE|LAW)\]", "", text).strip()


    def pdf_to_mongodb(self, data: bytes, filename: str, max_workers=4, chunk_size=50) -> list:
        """Convert PDF bytes into page images and upload to MongoDB using PyMuPDF."""
        print("[DEBUG] Opening PDF with PyMuPDF...")
        doc = fitz.open(stream=data, filetype="pdf")
        total_pages = len(doc)
        image_ids = []

        print(f"[DEBUG] Total pages detected: {total_pages}")
        print("[DEBUG] Splitting into chunks...")

        # Process in chunks
        for start in range(0, total_pages, chunk_size):
            end = min(start + chunk_size, total_pages)
            print(f"[DEBUG] Processing pages {start} to {end - 1}")

            # Convert each page to image (pixmap)
            pages = []
            for i in range(start, end):
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=200)   # good quality for OCR
                img_bytes = pix.tobytes("png")   # raw PNG bytes
                pages.append((i, img_bytes))

            # Map to _process_page using thread pool
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        self._process_page,
                        page_index,
                        Image.open(BytesIO(img_bytes)),  # convert to PIL Image
                        filename
                    )
                    for page_index, img_bytes in pages
                ]

                for future in futures:
                    image_ids.append(future.result())

        doc.close()
        return image_ids
    
    def get_data(self) -> List[dict]:
        """ Method to perform a read and retrieve data from MongoDB database for weaviate meta data to reference """
        one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        text = ExtractedText.objects(time_stamp__gte=one_hour_ago)
        if not text:
            print("No data found")
        else:
            print("Data found:", text)
        data = [
            {
                'text_data' : self._clean_tags(t.text),
                'doc_data' : str(t.image.filename) if t.image else None,
                'image_data' : str(t.image.image_id) if t.image else None,
            }
            for t in text if not self._is_noisy(t.text)
        ]
        return data

    def store_data(self,data: List[dict], client: WeaviateClient):
        """ Method to store data in weaviate database through batches"""
        embeddings = client.collections.get("Vectorbase")
        # batch system to dynamically set batch sizes for insertion of data as it is effecient to batch large amounts of data instead of passing it as an object.
        with embeddings.batch.dynamic() as batch:
            for i,item in tqdm(enumerate(data)):
                query_params = {
                    'embed_type':'document',
                }
                embedding_response = requests.post("http://localhost:8081/vectors",params=query_params,json={"text":[item['text_data']]})
                vector = embedding_response.json()

                doc_obj = {
                    "text" : item['text_data'],
                    "doc_name" : item['doc_data'],
                    "image_id" : str(item['image_data']),
                }

                batch.add_object(
                    properties=doc_obj,
                    vector=vector["vectors"][0],
                    uuid = str(uuid.uuid4())
                )
        if len(embeddings.batch.failed_objects) > 0:
            print(f"Failed to import {len(embeddings.batch.failed_objects)} objects")

    @staticmethod
    def create_weaviate_schema(client: WeaviateClient):
        """Create a weaviate database collection with a defined schema."""
        try:
            existing_collections = [col.name for col in client.collections.list_all()]
            if "Vectorbase" in existing_collections:
                print("Collection 'Vectorbase' already exists. Skipping creation.")

            else:
                client.collections.create(
                    name="Vectorbase",
                    properties=[
                        wc.Property(name="text",data_type=wc.DataType.TEXT),
                        wc.Property(name="doc_name",data_type=wc.DataType.TEXT),
                        wc.Property(name="image_id",data_type=wc.DataType.TEXT),
                    ],
                vector_config= wc.Configure.Vectors.self_provided(),
                )
        except Exception as e:
            print(f"Exception Occured : {e}")
