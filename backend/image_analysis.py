from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from backend.auth import User, get_current_user
from pydantic import BaseModel
import os
import hashlib
import base64
import logging
from datetime import datetime
import re
import uuid
from openai import AsyncOpenAI
from google.cloud import vision
from google.cloud.vision_v1 import types
from dotenv import load_dotenv
import mimetypes
import io
from PIL import Image
import numpy as np
import cv2
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load environment variables
from dotenv import load_dotenv
import os
from openai import AsyncOpenAI
from google.cloud import vision

# Load environment variables from .env file
load_dotenv()

# Set Google Cloud Vision credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if not os.environ["GOOGLE_APPLICATION_CREDENTIALS"]:
    raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not found in environment variables")\

print("🔑 GOOGLE_APPLICATION_CREDENTIALS =", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))


# Set OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not found in environment variables")

# Initialize OpenAI and Vision clients
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
vision_client = vision.ImageAnnotatorClient()
print(vision_client)


# Configuration
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15MB for higher resolution images
ALLOWED_IMAGE_TYPES = [
    "image/jpeg", "image/png", "image/gif", "image/bmp", "image/dicom",
    "image/tiff", "image/webp"
]
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Enhanced logging
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.INFO)

# Comprehensive specialty keywords for improved detection
SPECIALTY_KEYWORDS = {
    # Dermatology
    "skin": "Dermatologist", "rash": "Dermatologist", "mole": "Dermatologist", "lesion": "Dermatologist",
    "dermatitis": "Dermatologist", "psoriasis": "Dermatologist", "eczema": "Dermatologist",
    "melanoma": "Dermatologist", "basal cell carcinoma": "Dermatologist", "squamous cell carcinoma": "Dermatologist",
    "ulcer": "Dermatologist", "pigmentation": "Dermatologist", "erythema": "Dermatologist",
    "papule": "Dermatologist", "nodule": "Dermatologist", "plaque": "Dermatologist",
    "vesicle": "Dermatologist", "pustule": "Dermatologist", "blister": "Dermatologist",
    "acne": "Dermatologist", "rosacea": "Dermatologist", "vitiligo": "Dermatologist",
    "herpes": "Dermatologist", "wart": "Dermatologist", "fungal": "Dermatologist",
    "scabies": "Dermatologist", "lichen": "Dermatologist", "keratosis": "Dermatologist",

    # Orthopedics
    "bone": "Orthopedist", "fracture": "Orthopedist", "joint": "Orthopedist", "spine": "Orthopedist",
    "dislocation": "Orthopedist", "arthritis": "Orthopedist", "tendon": "Orthopedist",
    "ligament": "Orthopedist", "cartilage": "Orthopedist", "osteoporosis": "Orthopedist",
    "scoliosis": "Orthopedist", "kyphosis": "Orthopedist", "spondylosis": "Orthopedist",
    "herniated disc": "Orthopedist", "meniscus": "Orthopedist", "rotator cuff": "Orthopedist",
    "bunion": "Orthopedist", "hammertoe": "Orthopedist", "plantar fasciitis": "Orthopedist",

    # Pulmonology
    "lung": "Pulmonologist", "chest": "Pulmonologist", "pneumonia": "Pulmonologist",
    "bronchitis": "Pulmonologist", "pleural": "Pulmonologist", "emphysema": "Pulmonologist",
    "tuberculosis": "Pulmonologist", "copd": "Pulmonologist", "infiltrate": "Pulmonologist",
    "ground glass": "Pulmonologist", "consolidation": "Pulmonologist", "effusion": "Pulmonologist",
    "pneumothorax": "Pulmonologist", "hemothorax": "Pulmonologist", "atelectasis": "Pulmonologist",
    "bronchiectasis": "Pulmonologist", "pulmonary edema": "Pulmonologist", "fibrosis": "Pulmonologist",
    "sarcoidosis": "Pulmonologist", "asthma": "Pulmonologist", "cystic fibrosis": "Pulmonologist",

    # Cardiology
    "heart": "Cardiologist", "cardiac": "Cardiologist", "coronary": "Cardiologist",
    "valve": "Cardiologist", "aorta": "Cardiologist", "cardiomegaly": "Cardiologist",
    "arrhythmia": "Cardiologist", "myocardium": "Cardiologist", "pericardium": "Cardiologist",
    "stenosis": "Cardiologist", "regurgitation": "Cardiologist", "aneurysm": "Cardiologist",
    "ischemia": "Cardiologist", "infarction": "Cardiologist", "angina": "Cardiologist",
    "hypertrophy": "Cardiologist", "atrial": "Cardiologist", "ventricular": "Cardiologist",

    # Neurology
    "brain": "Neurologist", "head": "Neurologist", "nerve": "Neurologist", "stroke": "Neurologist",
    "cerebral": "Neurologist", "tumor": "Neurologist", "multiple sclerosis": "Neurologist",
    "seizure": "Neurologist", "epilepsy": "Neurologist", "meningitis": "Neurologist",
    "encephalitis": "Neurologist", "dementia": "Neurologist", "parkinson": "Neurologist",
    "neuropathy": "Neurologist", "myopathy": "Neurologist", "glioma": "Neurologist",
    "hemorrhage": "Neurologist", "edema": "Neurologist", "hydrocephalus": "Neurologist",

    # Radiology
    "x-ray": "Radiologist", "mri": "Radiologist", "ct scan": "Radiologist", "ultrasound": "Radiologist",
    "radiograph": "Radiologist", "density": "Radiologist", "opacity": "Radiologist",
    "contrast": "Radiologist", "pet scan": "Radiologist", "mammogram": "Radiologist",
    "fluoroscopy": "Radiologist", "angiogram": "Radiologist", "doppler": "Radiologist",

    # Oncology
    "cancer": "Oncologist", "tumor": "Oncologist", "mass": "Oncologist", "malignancy": "Oncologist",
    "lymphoma": "Oncologist", "carcinoma": "Oncologist", "sarcoma": "Oncologist",
    "metastasis": "Oncologist", "leukemia": "Oncologist", "myeloma": "Oncologist",
    "adenoma": "Oncologist", "neoplasm": "Oncologist", "chemotherapy": "Oncologist",

    # Gastroenterology
    "stomach": "Gastroenterologist", "liver": "Gastroenterologist", "intestine": "Gastroenterologist",
    "colon": "Gastroenterologist", "esophagus": "Gastroenterologist", "pancreas": "Gastroenterologist",
    "gallbladder": "Gastroenterologist", "ulcer": "Gastroenterologist", "gastritis": "Gastroenterologist",
    "colitis": "Gastroenterologist", "crohn": "Gastroenterologist", "diverticulitis": "Gastroenterologist",
    "hepatitis": "Gastroenterologist", "cirrhosis": "Gastroenterologist", "cholecystitis": "Gastroenterologist",

    # Ophthalmology
    "eye": "Ophthalmologist", "retina": "Ophthalmologist", "cornea": "Ophthalmologist",
    "cataract": "Ophthalmologist", "glaucoma": "Ophthalmologist", "macula": "Ophthalmologist",
    "optic": "Ophthalmologist", "conjunctivitis": "Ophthalmologist", "keratitis": "Ophthalmologist",

    # Endocrinology
    "thyroid": "Endocrinologist", "diabetes": "Endocrinologist", "hormone": "Endocrinologist",
    "adrenal": "Endocrinologist", "pituitary": "Endocrinologist", "goiter": "Endocrinologist",
    "hyperthyroidism": "Endocrinologist", "hypothyroidism": "Endocrinologist", "cushing": "Endocrinologist",

    # Urology
    "kidney": "Urologist", "bladder": "Urologist", "prostate": "Urologist", "ureter": "Urologist",
    "urethra": "Urologist", "stone": "Urologist", "hydronephrosis": "Urologist",
    "cystitis": "Urologist", "incontinence": "Urologist", "hematuria": "Urologist",

    # Infectious Diseases
    "infection": "Infectious Disease Specialist", "bacterial": "Infectious Disease Specialist",
    "viral": "Infectious Disease Specialist", "fungal": "Infectious Disease Specialist",
    "parasitic": "Infectious Disease Specialist", "sepsis": "Infectious Disease Specialist",
    "abscess": "Infectious Disease Specialist", "meningitis": "Infectious Disease Specialist",
}

# Comprehensive image classification map
IMAGE_TYPE_CLASSIFICATION = {
    "x-ray": [
        "bone", "chest", "radiograph", "x-ray", "thorax", "skeletal", "fracture", "joint",
        "spine", "rib", "clavicle", "pelvis", "femur", "tibia", "humerus", "skull",
        "dental", "mandible", "maxilla", "sinus"
    ],
    "mri": [
        "mri", "magnetic resonance", "t1", "t2", "flair", "diffusion", "weighted",
        "brain", "spine", "knee", "shoulder", "hip", "ankle", "wrist", "sagittal",
        "coronal", "axial"
    ],
    "ct_scan": [
        "ct", "computed tomography", "cat scan", "contrast", "abdomen", "pelvis",
        "chest", "head", "sinus", "spine", "neck", "angiography", "coronary",
        "pulmonary", "renal"
    ],
    "ultrasound": [
        "ultrasound", "sonogram", "doppler", "echo", "fetal", "abdominal", "pelvic",
        "thyroid", "breast", "cardiac", "vascular", "renal", "liver", "gallbladder",
        "spleen", "pancreas"
    ],
    "dermatological": [
        "skin", "rash", "mole", "lesion", "wound", "dermatological", "pigmentation",
        "erythema", "papule", "nodule", "plaque", "vesicle", "pustule", "blister",
        "ulcer", "melanoma", "carcinoma", "eczema", "psoriasis", "acne", "rosacea",
        "vitiligo", "herpes", "wart", "fungal", "scabies", "lichen", "keratosis"
    ],
    "pathology": [
        "slide", "cell", "tissue", "biopsy", "stain", "histology", "cytology",
        "microscope", "hematoxylin", "eosin", "pathological", "malignant", "benign",
        "neoplastic", "inflammatory"
    ],
    "endoscopy": [
        "endoscopy", "colonoscopy", "gastroscopy", "bronchoscopy", "esophagus",
        "stomach", "colon", "rectum", "bronchus", "larynx", "polyp", "ulcer",
        "erosion", "mucosa"
    ],
    "ophthalmology": [
        "eye", "retina", "cornea", "fundus", "macula", "optic disc", "lens",
        "cataract", "glaucoma", "retinal detachment", "macular degeneration",
        "fluorescein", "angiography"
    ],
    "mammogram": [
        "mammogram", "breast", "calcification", "mass", "density", "asymmetry",
        "ductal", "lobular", "cyst", "fibroadenoma"
    ],
}

# Pydantic models for structured responses
class MedicalFinding(BaseModel):
    description: str
    location: str
    significance: str

class DifferentialDiagnosis(BaseModel):
    diagnosis: str
    likelihood: str
    reasoning: str

class HealthResponse(BaseModel):
    image_type: str
    findings: List[MedicalFinding]
    primary_diagnosis: str
    differential_diagnoses: List[DifferentialDiagnosis]
    severity: str
    recommended_specialist: str
    recommended_tests: List[str]
    confidence: float
    warning_notes: Optional[str] = None
    image_quality: Optional[str] = None

# Router setup
router = APIRouter()

# Enhanced secure filename function
def secure_filename(filename: str) -> str:
    base = os.path.basename(filename)
    name, ext = os.path.splitext(base)
    timestamp = datetime.now().timestamp()
    unique_id = uuid.uuid4().hex[:8]
    hash_obj = hashlib.sha256(f"{name}{timestamp}{unique_id}".encode())
    return f"{hash_obj.hexdigest()[:16]}{ext}"

# Image quality assessment
def assess_image_quality(contents: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(contents))
        image_array = np.array(image)
        
        # Check resolution
        width, height = image.size
        resolution = width * height
        if resolution < 300 * 300:
            return "Low resolution - may affect analysis accuracy"
        
        # Check brightness and contrast
        brightness = np.mean(image_array)
        if brightness < 50 or brightness > 200:
            return "Poor lighting - may affect analysis accuracy"
        
        # Check sharpness (using Laplacian variance)
        if len(image_array.shape) == 3:
            gray = np.mean(image_array, axis=2).astype(np.uint8)
        else:
            gray = image_array
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < 100:
            return "Blurry image - may affect analysis accuracy"
        
        return "Good quality"
    except Exception as e:
        logger.warning(f"Image quality assessment failed: {str(e)}")
        return "Unable to assess quality"

# Determine image type with higher accuracy
def determine_image_type(labels: List[str], objects: List[str], text: str) -> str:
    combined_text = " ".join(labels + objects + [text]).lower()
    
    # Score each image type
    scores = {img_type: 0 for img_type in IMAGE_TYPE_CLASSIFICATION}
    
    for img_type, keywords in IMAGE_TYPE_CLASSIFICATION.items():
        for keyword in keywords:
            if keyword in combined_text:
                scores[img_type] += 1
    
    # Get highest scoring type
    if max(scores.values(), default=0) > 0:
        return max(scores.items(), key=lambda x: x[1])[0]
    
    # Fallback to generic medical image
    return "medical_image"

# Enhanced image analysis function using GPT-4o
async def analyze_medical_image(contents: bytes, file_type: str) -> HealthResponse:
    try:
        logger.info("Starting medical image analysis")
        
        # Assess image quality
        image_quality = assess_image_quality(contents)
        logger.info(f"Image quality: {image_quality}")
        
        # Google Vision API analysis
        image = types.Image(content=contents)
        label_response = vision_client.label_detection(image=image)
        labels = [label.description.lower() for label in label_response.label_annotations]
        
        object_response = vision_client.object_localization(image=image)
        objects = [obj.name.lower() for obj in object_response.localized_object_annotations]
        
        text_response = vision_client.text_detection(image=image)
        extracted_text = text_response.text_annotations[0].description.lower() if text_response.text_annotations else ""

        # Log initial processing results
        logger.info(f"Vision API results - Labels: {len(labels)}, Objects: {len(objects)}, Text extracted: {len(extracted_text) > 0}")
        
        # Prepare image for OpenAI
        base64_image = base64.b64encode(contents).decode("utf-8")
        content_type = file_type or "image/jpeg"
        image_url = f"data:{content_type};base64,{base64_image}"
        
        # Determine image type with enhanced algorithm
        image_type_raw = determine_image_type(labels, objects, extracted_text)
        image_type_mapping = {
            "x-ray": "X-ray radiograph",
            "mri": "MRI scan",
            "ct_scan": "CT scan",
            "ultrasound": "Ultrasound image",
            "dermatological": "Dermatological image",
            "pathology": "Pathology slide",
            "endoscopy": "Endoscopic image",
            "ophthalmology": "Ophthalmological image",
            "mammogram": "Mammogram",
            "medical_image": "Medical image"
        }
        image_type_display = image_type_mapping.get(image_type_raw, "Medical image")
        
        logger.info(f"Detected image type: {image_type_display}")
        
        # Enhanced system prompt for GPT-4o with domain-specific guidance
        system_prompt = f"""
        You are a world-class medical imaging expert with fellowship training in radiology, dermatology, pathology, and other relevant specialties. You are equipped to interpret all types of medical images with clinical precision, using a systematic, evidence-based approach. Your goal is to provide a detailed, accurate, and actionable analysis of the provided medical image.

        TASK: Analyze the provided {image_type_display} with the highest level of clinical precision:

        ANALYSIS REQUIREMENTS:
        1. Confirm the type of medical image (e.g., X-ray, MRI, CT, ultrasound, dermatological photo, pathology slide, endoscopic image, ophthalmological image, mammogram).
        2. Use standardized medical terminology and a systematic approach specific to the modality:
           - For X-rays: Assess lung fields, cardiac silhouette, pleural spaces, diaphragm, bony structures systematically.
           - For MRI/CT: Note density/signal differences, structures involved, anatomical relationships.
           - For dermatological images: Evaluate using ABCDE criteria (Asymmetry, Border, Color, Diameter, Evolving), note pattern, distribution, color, texture, borders.
           - For pathology slides: Describe cellular morphology, staining patterns, and tissue architecture.
           - For endoscopic images: Assess mucosal appearance, presence of ulcers, erosions, polyps, or masses.
           - For ophthalmological images: Evaluate retina, optic disc, macula, and vascular patterns.
           - For mammograms: Assess for masses, calcifications, asymmetry, and architectural distortion.
        3. Identify both normal and abnormal findings with precise medical terminology.
        4. Relate findings to anatomical regions using accurate language.
        5. Consider patient safety: If findings suggest a potentially serious condition (e.g., malignancy, infection, fracture), prioritize urgency in recommendations.

        FORMAT YOUR RESPONSE WITH THESE EXACT SECTIONS:
        - IMAGE TYPE: [What type of medical image - be specific]
        - KEY FINDINGS: [List 3-5 most important findings with anatomical locations]
        - PRIMARY IMPRESSION: [Most likely diagnosis based on findings]
        - DIFFERENTIAL DIAGNOSES: [2-3 other possibilities with brief rationale]
        - SEVERITY ASSESSMENT: [low/moderate/high with brief justification]
        - RECOMMENDED SPECIALIST: [Most appropriate medical specialty]
        - SUGGESTED FOLLOW-UP: [Additional tests or imaging to confirm diagnosis]
        - CONFIDENCE LEVEL: [very low/low/moderate/high/very high - be realistic based on image quality and findings]

        Computer vision preprocessing detected:
        - Labels: {', '.join(labels[:10] if labels else ['none detected'])}
        - Objects: {', '.join(objects[:5] if objects else ['none detected'])}
        - Text: {extracted_text[:100] + '...' if len(extracted_text) > 100 else extracted_text if extracted_text else 'none detected'}

        Image quality assessment: {image_quality}

        CRITICAL GUIDELINES:
        1. For chest X-rays:
           - Comment on heart size, lung fields, costophrenic angles, and bony structures.
           - If increased opacity or infiltrates are present, consider pneumonia, atelectasis, effusion, or COVID-19 (e.g., ground glass opacities, bilateral infiltrates).
        2. For dermatological images:
           - Use ABCDE criteria for potential melanoma.
           - Consider common conditions (e.g., eczema, psoriasis, fungal infections) and serious conditions (e.g., melanoma, squamous cell carcinoma).
           - Note if the image lacks context (e.g., scale, surrounding skin) and how this impacts the assessment.
        3. For pathology slides:
           - Describe cellular atypia, mitotic figures, necrosis, and inflammatory infiltrates.
           - Differentiate between benign, malignant, and inflammatory processes.
        4. For endoscopic images:
           - Look for signs of inflammation, ulceration, bleeding, or masses.
           - Consider conditions like gastritis, colitis, or malignancy.
        5. For ophthalmological images:
           - Assess for signs of glaucoma (e.g., optic disc cupping), macular degeneration, or retinal detachment.
        6. For mammograms:
           - Look for masses, calcifications, or architectural distortion suggestive of breast cancer.
        7. If the image quality is suboptimal (e.g., blurry, low resolution, poor lighting), explain how this limits your assessment and adjust confidence accordingly.
        8. If the image is not a medical image, clearly state this and describe what the image shows.
        9. If no abnormalities are detected, state this clearly and recommend routine follow-up if appropriate.
        10. BE PRECISE, PROFESSIONAL, AND THOROUGH. Avoid speculative diagnoses without evidence.
        """

        # Call GPT-4o with optimized parameters
        logger.info("Calling GPT-4o for analysis")
        response = await openai_client.chat.completions.create(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]}
            ],
            max_tokens=1500,
            temperature=0.1,
            top_p=0.9,
            presence_penalty=0.2,
            frequency_penalty=0.3
        )

        response_text = response.choices[0].message.content.strip()
        logger.info(f"Received GPT-4o response of {len(response_text)} chars")

        # Enhanced extraction with error handling
        def extract(pattern, fallback="Unknown"):
            match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
            return match.group(1).strip() if match else fallback

        # Extract structured data
        image_type_extracted = extract(r"IMAGE TYPE:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "Unknown")
        key_findings_text = extract(r"KEY FINDINGS:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "No key findings identified.")
        primary_impression = extract(r"PRIMARY IMPRESSION:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "Unclear from image")
        differential_text = extract(r"DIFFERENTIAL DIAGNOSES:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "No alternative diagnoses provided")
        severity_assessment = extract(r"SEVERITY ASSESSMENT:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "low")
        specialty = extract(r"RECOMMENDED SPECIALIST:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "General Practitioner")
        follow_up = extract(r"SUGGESTED FOLLOW-UP:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "Consult with primary care physician")
        confidence_text = extract(r"CONFIDENCE LEVEL:\s*(.+?)(?=\n\s*-|\n\s*$|$)", "low").lower()

        # Define combined_text here to ensure it's always available
        combined_text = (primary_impression + " " + key_findings_text).lower()
        logger.info(f"Combined text for specialty detection: {combined_text[:100]}...")

        # Parse findings into structured format
        findings_list = []
        for finding in re.split(r'(?:\d+\.\s*|\n\s*-\s*|\n\s*•\s*)', key_findings_text):
            finding = finding.strip()
            if finding:
                location_match = re.search(r'(?:in|at|of|on)\s+the\s+([^\.;]+)', finding)
                location = location_match.group(1) if location_match else "Unspecified"
                
                significance = "Normal"
                if any(term in finding.lower() for term in ["abnormal", "concerning", "suspicious", "pathological"]):
                    significance = "Abnormal"
                
                findings_list.append(MedicalFinding(
                    description=finding,
                    location=location,
                    significance=significance
                ))
        
        # Parse differential diagnoses
        differential_list = []
        for diff_diag in re.split(r'(?:\d+\.\s*|\n\s*-\s*|\n\s*•\s*)', differential_text):
            diff_diag = diff_diag.strip()
            if diff_diag:
                diag_parts = diff_diag.split(":", 1)
                if len(diag_parts) > 1:
                    diagnosis, reasoning = diag_parts[0].strip(), diag_parts[1].strip()
                else:
                    diagnosis, reasoning = diff_diag, "Based on image findings"
                
                likelihood = "Possible"
                if any(term in diff_diag.lower() for term in ["likely", "probable", "consistent with"]):
                    likelihood = "Likely"
                elif any(term in diff_diag.lower() for term in ["unlikely", "less likely", "less probable"]):
                    likelihood = "Unlikely"
                    
                differential_list.append(DifferentialDiagnosis(
                    diagnosis=diagnosis,
                    likelihood=likelihood,
                    reasoning=reasoning
                ))
        
        # Handle non-medical images with better detection
        if any(phrase in response_text.lower() for phrase in ["not a medical image", "unable to identify", "not a diagnostic"]):
            logger.warning("Non-medical image detected")
            return HealthResponse(
                image_type="Not a medical image",
                findings=[MedicalFinding(
                    description="Not a valid medical image for analysis",
                    location="N/A",
                    significance="N/A"
                )],
                primary_diagnosis="Not a medical image or unidentifiable content",
                differential_diagnoses=[],
                severity="low",
                recommended_specialist="General Practitioner",
                recommended_tests=["Professional medical evaluation if a medical concern exists"],
                confidence=0.0,
                warning_notes="The uploaded image does not appear to be a valid medical image for diagnostic purposes.",
                image_quality=image_quality
            )

        # Parse follow-up recommendations into a list
        recommended_tests = []
        for test in re.split(r'(?:\d+\.\s*|\n\s*-\s*|\n\s*•\s*|,\s*and\s*|,\s*|and\s*)', follow_up):
            test = test.strip()
            if test and not test.lower().startswith("consult") and len(test) > 3:
                recommended_tests.append(test)
        
        if not recommended_tests:
            recommended_tests = ["Consultation with the recommended specialist"]

        # Enhanced confidence and severity mapping
        confidence_map = {
            "very low": 10.0, "low": 25.0, "fairly low": 35.0,
            "moderate": 50.0, "medium": 50.0,
            "fairly high": 65.0, "high": 75.0, "very high": 90.0
        }
        
        confidence_text_lower = confidence_text.lower()
        confidence_numeric = 25.0  # Default
        
        for conf_term, conf_value in confidence_map.items():
            if conf_term in confidence_text_lower:
                confidence_numeric = conf_value
                break
        
        # Adjust confidence based on image quality
        if "poor" in image_quality.lower() or "low" in image_quality.lower() or "blurry" in image_quality.lower():
            confidence_numeric = max(10.0, confidence_numeric * 0.7)  # Reduce confidence for poor quality
        
        # Parse severity with more granularity
        severity = "low"  # Default
        severity_lower = severity_assessment.lower()
        if "low" in severity_lower:
            severity = "low"
        elif "moderate" in severity_lower:
            severity = "moderate"
        elif "high" in severity_lower or "severe" in severity_lower:
            severity = "high"
        
        # Adjust severity based on confidence and findings
        if confidence_numeric < 30 and severity == "high":
            severity = "moderate"  # Downgrade severity if confidence is very low
        if "unclear" in primary_impression.lower() and severity == "high":
            severity = "moderate"  # Downgrade severity for unclear diagnoses
        
        # Change 2: Auto-suggest multiple specialists
        if specialty == "General Practitioner" or specialty == "Unknown":
            recommended_specialist = ", ".join(sorted(set(re.findall("|".join(SPECIALTY_KEYWORDS.values()), combined_text))))
            if not recommended_specialist:
                recommended_specialist = "General Practitioner"
        else:
            recommended_specialist = specialty
        
        # Special case for dermatological images
        if "dermatological" in image_type_extracted.lower():
            if any(term in combined_text for term in ["melanoma", "carcinoma", "ulcer", "asymmetry", "irregular"]):
                recommended_specialist = "Dermatologist" if "Dermatologist" not in recommended_specialist else recommended_specialist
                if severity == "low":
                    severity = "moderate"  # Increase severity for potential malignancy
        
        # Special case for chest X-rays
        if "chest" in image_type_extracted.lower() and "x-ray" in image_type_extracted.lower():
            if any(term in key_findings_text.lower() for term in ["heart", "cardiomegaly", "enlarged cardiac"]):
                if "Cardiologist" not in recommended_specialist.lower():
                    recommended_specialist = f"{recommended_specialist}, Cardiologist or Pulmonologist"
            elif any(term in key_findings_text.lower() for term in ["pneumonia", "infiltrate", "consolidation", "opacity"]):
                if "Pulmonologist" not in recommended_specialist.lower():
                    recommended_specialist = f"{recommended_specialist}, Pulmonologist"
        
        logger.info(f"Analysis completed: Type={image_type_extracted}, Diagnosis={primary_impression}, Confidence={confidence_numeric}, Specialist={recommended_specialist}")

        # Return enhanced structured response
        return HealthResponse(
            image_type=image_type_extracted,
            findings=findings_list,
            primary_diagnosis=primary_impression,
            differential_diagnoses=differential_list,
            severity=severity,
            recommended_specialist=recommended_specialist,
            recommended_tests=recommended_tests,
            confidence=confidence_numeric,
            warning_notes="This is an AI-assisted analysis and should be reviewed by a qualified healthcare professional.",
            image_quality=image_quality
        )

    except Exception as e:
        logger.error(f"Image analysis error: {str(e)}", exc_info=True)
        return HealthResponse(
            image_type="Error",
            findings=[MedicalFinding(
                description=f"An error occurred during analysis: {str(e)}",
                location="N/A",
                significance="N/A"
            )],
            primary_diagnosis="Analysis error",
            differential_diagnoses=[],
            severity="low",
            recommended_specialist="General Practitioner",
            recommended_tests=["Professional medical evaluation"],
            confidence=0.0,
            warning_notes="There was a technical error during image processing. Please try again or consult a healthcare professional.",
            image_quality="Unknown"
        )

# Change 1: Fix 403 Forbidden by allowing anonymous access
@router.post("/image")
async def analyze_medical_image_route(
    file: UploadFile = File(...)
):
    """
    Endpoint to analyze medical images and provide diagnostic insights.
    
    - Accepts medical images (X-rays, CT scans, MRIs, dermatological photos, etc.)
    - Performs AI-assisted analysis using Google Vision API and GPT-4o
    - Returns structured diagnostic information and recommendations
    
    Note: Results are for informational purposes only and should be reviewed by a healthcare professional.
    """
    # Validate file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Only medical image files allowed ({', '.join(ALLOWED_IMAGE_TYPES)})"
        )
    
    # Read file content
    file_content = await file.read()
    
    # Check file size after reading
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Image size exceeds {MAX_FILE_SIZE // (1024 * 1024)}MB"
        )

    # Validate image format
    try:
        Image.open(io.BytesIO(file_content))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image format: {str(e)}"
        )

    # Save the file with secure name
    secure_name = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, secure_name)
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Generate image URL
    base_url = os.getenv("BASE_URL", "http://localhost:8000")
    image_url = f"{base_url}/{file_path}"

    # Analyze the image
    analysis_result = await analyze_medical_image(file_content, file.content_type)
    
    # Enhanced response structure
    response = {
        "success": True,
        "image_info": {
            "filename": secure_name,
            "image_url": image_url,
            "content_type": file.content_type,
            "size_kb": len(file_content) // 1024
        },
        "analysis": analysis_result.dict(),
        "disclaimer": "This AI-assisted analysis is for informational purposes only and should not replace professional medical advice or diagnosis."
    }
    
    return response

# Change 3: Add PDF report generator
@router.get("/image/report/{filename}")
def download_pdf(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    pdf_path = file_path + "_report.pdf"

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    c = canvas.Canvas(pdf_path, pagesize=letter)
    c.drawString(100, 750, "🩻 Health Assistant Report")
    c.drawString(100, 730, f"Image File: {filename}")
    c.drawString(100, 710, "Analysis Result: Please refer to the app UI.")
    c.drawImage(file_path, 100, 400, width=300, height=300, preserveAspectRatio=True)
    c.save()

    return FileResponse(pdf_path, filename="Health_Report.pdf", media_type="application/pdf")