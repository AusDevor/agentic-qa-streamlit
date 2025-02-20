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
from markitdown import MarkItDown
import os

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
doc_converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(
            backend=PyPdfiumDocumentBackend,
            pipeline_options=pipeline_options
        ),
    },
)


class SectionExtractor:
    
    def __init__(self, file_path):
        self.input_path = file_path 

    def generate_summary(self, section_content: str) -> dict:
        prompt = f"Summarize the following text and extract keywords:\n\n{section_content}"

        completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
        )

        summary = completion.choices[0].message.content.strip()

        return summary

    def extract_sections(self, markdown_text):
        
        heading_pattern = re.compile(r'^(#{1,6})\s(.+)', re.MULTILINE)

        sections = []
        current_section = None

        for match in heading_pattern.finditer(markdown_text):
            heading_level = len(match.group(1))
            heading_text = match.group(2)
            heading_start = match.start()

            # If there's a current section, close it
            if current_section:
                current_section['length'] = heading_start - current_section['start_index']
                current_section['text'] = markdown_text[current_section['start_index']:heading_start].strip()
                current_section['summary'] = ''#self.generate_summary(current_section['text'])
                current_section['context'] = current_section['text'][:200]
                sections.append(current_section)

            # Start a new section
            current_section = {
                'title': heading_text,
                'level': heading_level,
                'start_index': heading_start,
                'length': None,
                'text': None
            }

        # Add the last section
        if current_section:
            current_section['length'] = len(markdown_text) - current_section['start_index']
            current_section['text'] = markdown_text[current_section['start_index']:].strip()
            current_section['summary'] = ''#self.generate_summary(current_section['text'])
            current_section['context'] = current_section['text'][:200]
            sections.append(current_section)

        return sections
    
    def process(self):
        
        conv_res = doc_converter.convert(self.input_path)
        doc = conv_res.document
        markdown = doc.export_to_markdown()
        #md = MarkItDown()
        #markdown = md.convert(self.input_path)
        sections = self.extract_sections(markdown)
        
        return sections
