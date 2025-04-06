// src/pages/Doctors.tsx
import { useState, useRef, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import styles from "../styles/DoctorSearch.module.scss";
import DoctorCard from "../components/DoctorCard";
import { toast } from "react-toastify";

interface Doctor {
  name: string;
  specialty: string;
  address: string;
  phone: string | null;
  website: string | null;
}

const Doctors = () => {
  const [searchParams] = useSearchParams();
  const specialtyFromUrl = searchParams.get("specialty");
  const locationFromUrl = searchParams.get("location");

  const [specialty, setSpecialty] = useState("");
  const [location, setLocation] = useState("");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [notFound, setNotFound] = useState(false);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const observer = useRef<IntersectionObserver | null>(null);
  const endRef = useRef<HTMLDivElement | null>(null);

  const handleSearch = async (reset = true, specialtyParam?: string, locationParam?: string) => {
    const searchSpecialty = specialtyParam ?? specialty;
    const searchLocation = locationParam ?? location;

    if (!searchSpecialty || !searchLocation) return;
    setLoading(true);
    setNotFound(false);

    if (reset) {
      setDoctors([]);
      setPage(1);
    }

    try {
      const token = localStorage.getItem("access_token");
      const response = await fetch(
        `http://127.0.0.1:8000/health/doctor-search?specialty=${searchSpecialty}&location=${searchLocation}&page=${
          reset ? 1 : page
        }&page_size=10`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      const data = await response.json();

      if (response.ok && data.results?.length > 0) {
        setDoctors((prev) => [...prev, ...data.results]);
        setHasMore(data.results.length === 10);
      } else {
        setHasMore(false);
        if (reset) setNotFound(true);
      }
    } catch (error) {
      toast.error("Search failed.");
      setNotFound(true);
    } finally {
      setLoading(false);
    }
  };

  // Infinite scroll trigger
  useEffect(() => {
    if (!hasMore || loading || page === 1) return;
    handleSearch(false);
  }, [page]);

  useEffect(() => {
    if (observer.current) observer.current.disconnect();
    observer.current = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        setPage((prev) => prev + 1);
      }
    });
    if (endRef.current) observer.current.observe(endRef.current);
  }, [doctors]);

  // Autofill input from URL
  useEffect(() => {
    if (specialtyFromUrl) setSpecialty(specialtyFromUrl);
    if (locationFromUrl && locationFromUrl !== "auto") setLocation(locationFromUrl);
  }, [specialtyFromUrl, locationFromUrl]);

  // Auto search on mount if query params exist
  useEffect(() => {
    if (specialtyFromUrl && locationFromUrl) {
      if (locationFromUrl === "auto") {
        navigator.geolocation.getCurrentPosition(
          async (pos) => {
            const coords = `${pos.coords.latitude},${pos.coords.longitude}`;
            await handleSearch(true, specialtyFromUrl, coords);
          },
          () => {
            toast.error("Failed to get your location.");
          }
        );
      } else {
        handleSearch(true, specialtyFromUrl, locationFromUrl);
      }
    }
  }, [specialtyFromUrl, locationFromUrl]);

  return (
    <div className={styles.doctorSearchPage}>
      <h2 className={styles.title}>🔍 Find Doctors</h2>

      <div className={styles.searchBar}>
        <input
          type="text"
          placeholder="Enter specialty (e.g. dentist)"
          value={specialty}
          onChange={(e) => setSpecialty(e.target.value)}
        />
        <input
          type="text"
          placeholder="Enter city or location"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <button onClick={() => handleSearch(true)} disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </div>

      {notFound && (
        <div className={styles.notFound}>No doctors found. Try another search.</div>
      )}

      <div className={styles.doctorGrid}>
        {doctors.map((doctor, index) => (
          <DoctorCard key={index} doctor={doctor} />
        ))}
        {loading && <p>Loading more doctors...</p>}
        <div ref={endRef} />
      </div>
    </div>
  );
};

export default Doctors;
