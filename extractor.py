from docling.datamodel.base_models import InputFormat
from docling.document_converter import *
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling_core.types.doc.document import DoclingDocument
from docling.pipeline.simple_pipeline import SimplePipeline
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline
from docling.datamodel.pipeline_options import (
    AcceleratorDevice,
    AcceleratorOptions,
    PdfPipelineOptions,
    TableFormerMode,
)
from docling.datamodel.settings import settings
from docling.backend.msword_backend import MsWordDocumentBackend
from docling.chunking import HybridChunker
import re
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Accelerator and pipeline options
accelerator_options = AcceleratorOptions(
    num_threads=16, device=AcceleratorDevice.CPU
)
pipeline_options = PdfPipelineOptions(do_table_structure=False, do_ocr=False)
pipeline_options.table_structure_options.do_cell_matching = False
pipeline_options.table_structure_options.mode = TableFormerMode.FAST
pipeline_options.accelerator_options = accelerator_options

# Document converter initialization
doc_converter = (
    DocumentConverter(  # all of the below is optional, has internal defaults.
        allowed_formats=[
            InputFormat.PDF,
            InputFormat.DOCX,
            InputFormat.HTML,
            InputFormat.MD,
        ],  # whitelist formats, non-matching files are ignored.
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_cls=StandardPdfPipeline, backend=PyPdfiumDocumentBackend
            ),
            InputFormat.DOCX: WordFormatOption(
                pipeline_cls=SimplePipeline,  backend=MsWordDocumentBackend
            ),
        },
    )
)


class SectionExtractor:
    
    def __init__(self, file_path):
        self.input_path = file_path 

    def generate_summary(self, section_content: str) -> dict:
        prompt = f"Summarize the following text and extract keywords:\n\n{section_content}"

        completion = client.chat.completions.create(
        model="o3-mini",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        )

        summary = completion.choices[0].message.content.strip()

        return summary
    
    def extract_sections_from_txt(self, text):
        sections = []
        lines = text.split("\n")

        current_title = None
        current_content = []
        current_start_index = 0

        for i, line in enumerate(lines):
            if len(line.strip()) < 30 and line.strip():  # Section title condition
                if current_title:  # Save the previous section
                    last_start_index = sections[len(sections)-1]['start_index'] if len(sections) > 0 else 0
                    summary = self.generate_summary("\n".join(current_content).strip())
                    sections.append({
                        "title": current_title,
                        "start_index": current_start_index,
                        "length": current_start_index - last_start_index,  # Calculate length
                        "text": "\n".join(current_content).strip(),
                        "summary": summary
                    })
                current_title = line.strip()
                current_content = []
                current_start_index += len(line)
            else:
                current_content.append(line)
                current_start_index += len(line)

        if current_title:
            last_start_index = sections[len(sections)-1]['start_index'] if len(sections) > 0 else 0
            summary = self.generate_summary("\n".join(current_content).strip())
            sections.append({
                "title": current_title,
                "start_index": current_start_index,
                "length": current_start_index - last_start_index, 
                "text": "\n".join(current_content).strip(),
                "summary": summary
            })

        return sections

    def extract_sections(self, markdown_text):
        
        heading_pattern = re.compile(r'^(#{1,6})\s(.+)', re.MULTILINE)

        sections = []
        current_section = None

        for match in heading_pattern.finditer(markdown_text):
            heading_text = match.group(2)
            heading_start = match.start()

            # If there's a current section, close it
            if current_section:
                current_section['length'] = heading_start - current_section['start_index']
                current_section['text'] = markdown_text[current_section['start_index']:heading_start].strip()
                current_section['summary'] = self.generate_summary(current_section['text'])
                # current_section['context'] = current_section['text'][:200]
                sections.append(current_section)

            # Start a new section
            current_section = {
                'title': heading_text,
                'start_index': heading_start,
                'length': None,
                'text': None,
                'summary': None
            }

        # Add the last section
        if current_section:
            current_section['length'] = len(markdown_text) - current_section['start_index']
            current_section['text'] = markdown_text[current_section['start_index']:].strip()
            current_section['summary'] = self.generate_summary(current_section['text'])
            #current_section['context'] = current_section['text'][:200]
            sections.append(current_section)

        return sections
    
    def process(self):
        
        file_extension = self.input_path.split(".")[-1]
        temp_path = f"temp/{self.input_path}"
        
        sections = None
        if file_extension == "txt" or file_extension == "doc":
            with open(temp_path, "r", encoding="utf-8") as file:
                content = file.read()
                sections = self.extract_sections_from_txt(content)
        else:
            conv_res = doc_converter.convert(temp_path)
            doc = conv_res.document
            markdown = doc.export_to_markdown()
            sections = self.extract_sections(markdown)
            
        for section in sections:
            section["file_path"] = self.input_path
            

        return sections
