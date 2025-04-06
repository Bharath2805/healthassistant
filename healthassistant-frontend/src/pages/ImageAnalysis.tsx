import { useState } from "react";
import styles from "../styles/ImageAnalysis.module.scss";
import { toast } from "react-toastify";

const ImageAnalysis = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setImagePreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return toast.error("Please select an image.");

    const formData = new FormData();
    formData.append("file", selectedFile);
    setLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/health/image", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      if (data.success) {
        setResult(data.analysis);
        toast.success("Analysis complete.");
      } else {
        toast.error("Analysis failed.");
      }
    } catch (err) {
      toast.error("Server error during analysis.");
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = () => {
    if (!result) return;
    window.open(`http://127.0.0.1:8000/health/image/report/${result?.image_name}`, "_blank");
  };

  const navigateToDoctorSearch = () => {
    if (!result?.recommended_specialist) return;

    // Clean up specialist name(s) for search
    const specialty = result.recommended_specialist
      .split(",")[0]
      .split(" ")[0]
      .toLowerCase();
    window.location.href = `/doctors?specialty=${encodeURIComponent(specialty)}&location=auto`;
  };

  return (
    <div className={styles.container}>
      <h1 className={styles.heading}>🖼️ Image Health Analysis</h1>

      <div className={styles.uploadBox}>
        <label htmlFor="fileInput">CLICK OR DRAG AN IMAGE HERE</label>
        <input
          id="fileInput"
          type="file"
          accept="image/*"
          onChange={handleFileChange}
        />
        {imagePreview && (
          <img src={imagePreview} alt="Preview" className={styles.preview} />
        )}
        <button className={styles.glowBtn} onClick={handleAnalyze} disabled={loading}>
          {loading ? "Analyzing..." : "Analyze Image"}
        </button>
      </div>

      {result && (
        <div className={styles.resultBox}>
          <h3 className={styles.resultTitle}>🧠 Diagnosis Result</h3>
          <p><strong>Diagnosis:</strong> {result.primary_diagnosis}</p>
          <p><strong>Severity:</strong> {result.severity}</p>
          <p><strong>Confidence:</strong> {result.confidence}%</p>
          <p><strong>Recommended Specialist(s):</strong> {result.recommended_specialist}</p>
          <p className={styles.disclaimer}>
            {result.warning_notes || "This is an AI-assisted analysis and should be reviewed by a qualified healthcare professional."}
          </p>
          <div className={styles.buttonGroup}>
            <button className={styles.glowBtn} onClick={navigateToDoctorSearch}>
              🩺 Find Nearby {result.recommended_specialist.split(",")[0]}
            </button>
            <button className={styles.glowBtn} onClick={downloadReport}>
              📄 Download Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ImageAnalysis;
