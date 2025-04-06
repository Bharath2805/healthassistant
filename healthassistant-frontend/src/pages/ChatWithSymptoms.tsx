import { useState } from "react";
import styles from "../styles/ChatWithSymptoms.module.scss";
import { toast } from "react-toastify";
import { FaBrain, FaRedoAlt, FaTimes, FaSpinner } from "react-icons/fa";

const ChatWithSymptoms = () => {
  const [symptoms, setSymptoms] = useState([""]);
  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (index: number, value: string) => {
    const updated = [...symptoms];
    updated[index] = value;
    setSymptoms(updated);
  };

  const addSymptom = () => setSymptoms([...symptoms, ""]);
  const removeSymptom = (index: number) => {
    const updated = symptoms.filter((_, i) => i !== index);
    setSymptoms(updated.length > 0 ? updated : [""]);
  };

  const resetSymptoms = () => {
    setSymptoms([""]);
    setResult(null);
    setLoading(false);
  };

  const handleSubmit = async () => {
    const validSymptoms = symptoms.filter((s) => s.trim() !== "");
    if (validSymptoms.length === 0) {
      toast.warn("Please enter at least one symptom.");
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const token = localStorage.getItem("access_token");
      const res = await fetch("http://127.0.0.1:8000/health/symptoms", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ symptoms: validSymptoms }),
      });

      if (!res.ok) throw new Error("Failed to submit symptoms");
      const data = await res.json();
      setResult(data.response);
    } catch (err) {
      console.error(err);
      toast.error("Something went wrong. Try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.symptomPage}>
      <div className={styles.title}>
        <FaBrain />
        Chat with Symptoms
      </div>

      {symptoms.map((symptom, idx) => (
        <div className={styles.symptomInputRow} key={idx}>
          <input
            type="text"
            className={styles.symptomInput}
            placeholder={`Symptom ${idx + 1}`}
            value={symptom}
            onChange={(e) => handleChange(idx, e.target.value)}
          />
          <button
            className={styles.removeButton}
            onClick={() => removeSymptom(idx)}
            title="Remove Symptom"
          >
            <FaTimes />
          </button>
        </div>
      ))}

      <button className={styles.actionButton} onClick={addSymptom}>
        + Add Symptom
      </button>
      <button className={styles.actionButton} onClick={handleSubmit} disabled={loading}>
        {loading ? <FaSpinner className={styles.spin} /> : "Submit Symptoms"}
      </button>
      <button className={styles.actionButton} onClick={resetSymptoms}>
        <FaRedoAlt style={{ marginRight: "5px" }} />
        Reset
      </button>

      {loading && (
        <div className={styles.resultCard}>
          <div className={styles.resultTitle}>
            <FaSpinner className={styles.spin} />
            Analyzing symptoms...
          </div>
        </div>
      )}

      {!loading && result && (
        <div className={styles.resultCard}>
          <div className={styles.resultTitle}>🧠 Diagnosis Result</div>
          <p><strong>Diagnosis:</strong> {result.diagnosis}</p>
          <p><strong>Description:</strong> {result.description}</p>
          <p><strong>Severity:</strong> {result.severity}</p>
          <p><strong>Recommended Specialist:</strong> {result.recommended_speciality}</p>
          <p><strong>Confidence:</strong> {(result.confidence * 100).toFixed(0)}%</p>
        </div>
      )}
    </div>
  );
};

export default ChatWithSymptoms;
