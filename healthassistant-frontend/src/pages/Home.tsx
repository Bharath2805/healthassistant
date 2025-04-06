// src/pages/Home.tsx
import { motion } from "framer-motion";
import "../styles/globals.scss";
import Navbar from "../components/Navbar";
import HeroDoctor from "../components/HeroDoctor";
import FeatureCard from "../components/FeatureCard";
import ReminderList from "../components/ReminderList";
import EmergencyCard from "../components/Emergency";


function Home() {
  return (
    <div className="home">
      <Navbar />
      <div className="home-content">
        <div className="welcome">
          <motion.h1
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            Welcome to Your Health Assistant
          </motion.h1>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.6 }}
          >
            Choose a service to get started.
          </motion.p>
        </div>

        <div className="dashboard-layout">
          <div className="left-panel">
            <HeroDoctor />
            <div className="features">
              <FeatureCard title="Check Symptoms" />
              <FeatureCard title="Find Doctors" />
              <FeatureCard title="Analyze Images" />
            </div>
          </div>

          <div className="right-panel">
            <ReminderList />
            <EmergencyCard />
          </div>
        </div>
      </div>
    </div>
  );
}

export default Home;
