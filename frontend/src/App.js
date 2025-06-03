import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const LOCATIONS = ["Mount Isa", "Moranbah", "Charters Towers"];
const VISA_STATUS_OPTIONS = [
  { value: "citizen", label: "Australian Citizen" },
  { value: "permanent", label: "Permanent Resident" },
  { value: "temporary", label: "Temporary Visa" },
  { value: "needs_sponsorship", label: "Needs Sponsorship" }
];
const RELOCATION_OPTIONS = [
  { value: "yes", label: "Yes" },
  { value: "no", label: "No" },
  { value: "maybe", label: "Maybe" }
];
const ENGLISH_LEVELS = [
  { value: "native", label: "Native" },
  { value: "fluent", label: "Fluent" },
  { value: "good", label: "Good" },
  { value: "basic", label: "Basic" }
];
const APPLICATION_STATUSES = [
  { value: "new", label: "New" },
  { value: "screening", label: "Screening" },
  { value: "interview", label: "Interview" },
  { value: "offer", label: "Offer" },
  { value: "hired", label: "Hired" },
  { value: "rejected", label: "Rejected" }
];
const INTERVIEW_TYPES = [
  { value: "phone", label: "Phone Interview" },
  { value: "video", label: "Video Interview" },
  { value: "in_person", label: "In-Person Interview" }
];
const INTERVIEW_STATUSES = [
  { value: "scheduled", label: "Scheduled" },
  { value: "completed", label: "Completed" },
  { value: "cancelled", label: "Cancelled" },
  { value: "rescheduled", label: "Rescheduled" }
];

function App() {
  const [currentView, setCurrentView] = useState("dashboard");
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [applications, setApplications] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [loading, setLoading] = useState(false);
  const [selectedItems, setSelectedItems] = useState([]);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [visaEvaluations, setVisaEvaluations] = useState({});

  // Fetch data functions
  const fetchJobs = async () => {
    try {
      const response = await axios.get(`${API}/jobs`);
      setJobs(response.data);
    } catch (error) {
      console.error("Error fetching jobs:", error);
    }
  };

  const fetchCandidates = async () => {
    try {
      const response = await axios.get(`${API}/candidates`);
      setCandidates(response.data);
    } catch (error) {
      console.error("Error fetching candidates:", error);
    }
  };

  const fetchApplications = async () => {
    try {
      const response = await axios.get(`${API}/applications`);
      setApplications(response.data);
    } catch (error) {
      console.error("Error fetching applications:", error);
    }
  };

  const fetchInterviews = async () => {
    try {
      const response = await axios.get(`${API}/interviews`);
      setInterviews(response.data);
    } catch (error) {
      console.error("Error fetching interviews:", error);
    }
  };

  const fetchVisaEvaluation = async (candidateId) => {
    try {
      const response = await axios.get(`${API}/candidates/${candidateId}/visa-evaluation`);
      setVisaEvaluations(prev => ({...prev, [candidateId]: response.data}));
      return response.data;
    } catch (error) {
      console.error("Error fetching visa evaluation:", error);
      return null;
    }
  };

  const uploadResume = async (candidateId, file) => {
    setUploadingResume(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await axios.post(`${API}/candidates/${candidateId}/upload-resume`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      await fetchCandidates(); // Refresh candidates to show updated data
      return response.data;
    } catch (error) {
      console.error("Error uploading resume:", error);
      throw error;
    } finally {
      setUploadingResume(false);
    }
  };

  useEffect(() => {
    fetchJobs();
    fetchCandidates();
    fetchApplications();
    fetchInterviews();
  }, []);

  // Navigation Component
  const Navigation = () => (
    <nav className="bg-blue-900 text-white p-4 shadow-lg">
      <div className="container mx-auto flex justify-between items-center">
        <h1 className="text-2xl font-bold">GRO Early Learning ATS</h1>
        <div className="flex space-x-4">
          <button
            onClick={() => setCurrentView("dashboard")}
            className={`px-4 py-2 rounded transition-colors ${
              currentView === "dashboard" ? "bg-blue-700" : "hover:bg-blue-800"
            }`}
          >
            Dashboard
          </button>
          <button
            onClick={() => setCurrentView("jobs")}
            className={`px-4 py-2 rounded transition-colors ${
              currentView === "jobs" ? "bg-blue-700" : "hover:bg-blue-800"
            }`}
          >
            Jobs
          </button>
          <button
            onClick={() => setCurrentView("candidates")}
            className={`px-4 py-2 rounded transition-colors ${
              currentView === "candidates" ? "bg-blue-700" : "hover:bg-blue-800"
            }`}
          >
            Candidates
          </button>
          <button
            onClick={() => setCurrentView("applications")}
            className={`px-4 py-2 rounded transition-colors ${
              currentView === "applications" ? "bg-blue-700" : "hover:bg-blue-800"
            }`}
          >
            Applications
          </button>
        </div>
      </div>
    </nav>
  );

  // Dashboard Component
  const Dashboard = () => (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-800 mb-6">Dashboard Overview</h2>
      
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-blue-500">
          <h3 className="text-lg font-semibold text-gray-700">Active Jobs</h3>
          <p className="text-3xl font-bold text-blue-600">{dashboardStats.total_jobs || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-green-500">
          <h3 className="text-lg font-semibold text-gray-700">Total Candidates</h3>
          <p className="text-3xl font-bold text-green-600">{dashboardStats.total_candidates || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-yellow-500">
          <h3 className="text-lg font-semibold text-gray-700">Applications</h3>
          <p className="text-3xl font-bold text-yellow-600">{dashboardStats.total_applications || 0}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md border-l-4 border-purple-500">
          <h3 className="text-lg font-semibold text-gray-700">Visa Sponsorship</h3>
          <p className="text-3xl font-bold text-purple-600">
            {dashboardStats.visa_sponsorship?.true || 0}
          </p>
        </div>
      </div>

      {/* Application Status Breakdown */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Application Pipeline</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {APPLICATION_STATUSES.map(status => (
            <div key={status.value} className="text-center">
              <div className="bg-gray-100 p-4 rounded-lg">
                <p className="text-sm text-gray-600">{status.label}</p>
                <p className="text-2xl font-bold text-gray-800">
                  {dashboardStats.applications_by_status?.[status.value] || 0}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Location Distribution */}
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Jobs by Location</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {LOCATIONS.map(location => (
            <div key={location} className="text-center bg-gray-50 p-4 rounded-lg">
              <p className="text-lg font-semibold text-gray-700">{location}</p>
              <p className="text-2xl font-bold text-blue-600">
                {dashboardStats.jobs_by_location?.[location] || 0}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Job Management Component
  const JobManagement = () => {
    const [showJobForm, setShowJobForm] = useState(false);
    const [editingJob, setEditingJob] = useState(null);
    const [jobForm, setJobForm] = useState({
      title: "",
      location: "Mount Isa",
      sponsorship_eligible: false,
      relocation_support: false,
      housing_support: false,
      description: "",
      requirements: "",
      salary_range: "",
      employment_type: "Full-time"
    });

    const handleJobSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      
      try {
        const formData = {
          ...jobForm,
          requirements: jobForm.requirements.split('\n').filter(req => req.trim())
        };

        if (editingJob) {
          await axios.put(`${API}/jobs/${editingJob.id}`, formData);
        } else {
          await axios.post(`${API}/jobs`, formData);
        }
        
        await fetchJobs();
        await fetchInterviews();
        setShowJobForm(false);
        setEditingJob(null);
        setJobForm({
          title: "",
          location: "Mount Isa",
          sponsorship_eligible: false,
          relocation_support: false,
          housing_support: false,
          description: "",
          requirements: "",
          salary_range: "",
          employment_type: "Full-time"
        });
      } catch (error) {
        console.error("Error saving job:", error);
      } finally {
        setLoading(false);
      }
    };

    const editJob = (job) => {
      setEditingJob(job);
      setJobForm({
        ...job,
        requirements: job.requirements.join('\n')
      });
      setShowJobForm(true);
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold text-gray-800">Job Management</h2>
          <button
            onClick={() => setShowJobForm(!showJobForm)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            {showJobForm ? "Cancel" : "Create New Job"}
          </button>
        </div>

        {showJobForm && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4">
              {editingJob ? "Edit Job" : "Create New Job"}
            </h3>
            <form onSubmit={handleJobSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Job Title</label>
                <input
                  type="text"
                  value={jobForm.title}
                  onChange={(e) => setJobForm({...jobForm, title: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Location</label>
                <select
                  value={jobForm.location}
                  onChange={(e) => setJobForm({...jobForm, location: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {LOCATIONS.map(location => (
                    <option key={location} value={location}>{location}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salary Range</label>
                <input
                  type="text"
                  value={jobForm.salary_range}
                  onChange={(e) => setJobForm({...jobForm, salary_range: e.target.value})}
                  placeholder="e.g., $60,000 - $80,000 AUD"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Employment Type</label>
                <select
                  value={jobForm.employment_type}
                  onChange={(e) => setJobForm({...jobForm, employment_type: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Full-time">Full-time</option>
                  <option value="Part-time">Part-time</option>
                  <option value="Contract">Contract</option>
                  <option value="Casual">Casual</option>
                </select>
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Job Description</label>
                <textarea
                  value={jobForm.description}
                  onChange={(e) => setJobForm({...jobForm, description: e.target.value})}
                  rows="4"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Requirements (one per line)</label>
                <textarea
                  value={jobForm.requirements}
                  onChange={(e) => setJobForm({...jobForm, requirements: e.target.value})}
                  rows="3"
                  placeholder="Certificate III in Early Childhood Education&#10;Minimum 2 years experience&#10;Current Working with Children Check"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="md:col-span-2 space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={jobForm.sponsorship_eligible}
                    onChange={(e) => setJobForm({...jobForm, sponsorship_eligible: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Visa Sponsorship Available</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={jobForm.relocation_support}
                    onChange={(e) => setJobForm({...jobForm, relocation_support: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Relocation Support Provided</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={jobForm.housing_support}
                    onChange={(e) => setJobForm({...jobForm, housing_support: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Housing Support Available</span>
                </label>
              </div>
              
              <div className="md:col-span-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {loading ? "Saving..." : (editingJob ? "Update Job" : "Create Job")}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Jobs List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">Active Jobs</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sponsorship</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{job.title}</div>
                      <div className="text-sm text-gray-500">{job.employment_type}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{job.location}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        job.sponsorship_eligible 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {job.sponsorship_eligible ? 'Available' : 'Not Available'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(job.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => editJob(job)}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Candidate Management Component
  const CandidateManagement = () => {
    const [showCandidateForm, setShowCandidateForm] = useState(false);
    const [editingCandidate, setEditingCandidate] = useState(null);
    const [candidateForm, setCandidateForm] = useState({
      full_name: "",
      email: "",
      phone: "",
      location: "",
      visa_status: "citizen",
      visa_type: "",
      sponsorship_needed: false,
      childcare_cert: "",
      experience_years: 0,
      rural_experience: false,
      relocation_willing: "yes",
      housing_needed: false,
      english_level: "native",
      availability_start: "",
      salary_expectation: "",
      notes: ""
    });

    const handleCandidateSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      
      try {
        const formData = {
          ...candidateForm,
          experience_years: parseInt(candidateForm.experience_years) || 0,
          salary_expectation: candidateForm.salary_expectation ? parseInt(candidateForm.salary_expectation) : null,
          availability_start: candidateForm.availability_start || null
        };

        if (editingCandidate) {
          await axios.put(`${API}/candidates/${editingCandidate.id}`, formData);
        } else {
          await axios.post(`${API}/candidates`, formData);
        }
        
        await fetchCandidates();
        await fetchDashboardStats();
        setShowCandidateForm(false);
        setEditingCandidate(null);
        setCandidateForm({
          full_name: "",
          email: "",
          phone: "",
          location: "",
          visa_status: "citizen",
          visa_type: "",
          sponsorship_needed: false,
          childcare_cert: "",
          experience_years: 0,
          rural_experience: false,
          relocation_willing: "yes",
          housing_needed: false,
          english_level: "native",
          availability_start: "",
          salary_expectation: "",
          notes: ""
        });
      } catch (error) {
        console.error("Error saving candidate:", error);
      } finally {
        setLoading(false);
      }
    };

    const editCandidate = (candidate) => {
      setEditingCandidate(candidate);
      setCandidateForm({
        ...candidate,
        availability_start: candidate.availability_start ? candidate.availability_start.split('T')[0] : "",
        salary_expectation: candidate.salary_expectation || "",
        experience_years: candidate.experience_years || 0
      });
      setShowCandidateForm(true);
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold text-gray-800">Candidate Management</h2>
          <button
            onClick={() => setShowCandidateForm(!showCandidateForm)}
            className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors"
          >
            {showCandidateForm ? "Cancel" : "Add New Candidate"}
          </button>
        </div>

        {showCandidateForm && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4">
              {editingCandidate ? "Edit Candidate" : "Add New Candidate"}
            </h3>
            <form onSubmit={handleCandidateSubmit} className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={candidateForm.full_name}
                  onChange={(e) => setCandidateForm({...candidateForm, full_name: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={candidateForm.email}
                  onChange={(e) => setCandidateForm({...candidateForm, email: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Phone</label>
                <input
                  type="tel"
                  value={candidateForm.phone}
                  onChange={(e) => setCandidateForm({...candidateForm, phone: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Current Location</label>
                <input
                  type="text"
                  value={candidateForm.location}
                  onChange={(e) => setCandidateForm({...candidateForm, location: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                  required
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Visa Status</label>
                <select
                  value={candidateForm.visa_status}
                  onChange={(e) => setCandidateForm({...candidateForm, visa_status: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {VISA_STATUS_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Visa Type (if applicable)</label>
                <input
                  type="text"
                  value={candidateForm.visa_type}
                  onChange={(e) => setCandidateForm({...candidateForm, visa_type: e.target.value})}
                  placeholder="e.g., 482, 186, 494"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Childcare Certification</label>
                <input
                  type="text"
                  value={candidateForm.childcare_cert}
                  onChange={(e) => setCandidateForm({...candidateForm, childcare_cert: e.target.value})}
                  placeholder="e.g., Certificate III in Early Childhood Education"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Years of Experience</label>
                <input
                  type="number"
                  value={candidateForm.experience_years}
                  onChange={(e) => setCandidateForm({...candidateForm, experience_years: e.target.value})}
                  min="0"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">English Level</label>
                <select
                  value={candidateForm.english_level}
                  onChange={(e) => setCandidateForm({...candidateForm, english_level: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {ENGLISH_LEVELS.map(level => (
                    <option key={level.value} value={level.value}>{level.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Willing to Relocate</label>
                <select
                  value={candidateForm.relocation_willing}
                  onChange={(e) => setCandidateForm({...candidateForm, relocation_willing: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  {RELOCATION_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Available From</label>
                <input
                  type="date"
                  value={candidateForm.availability_start}
                  onChange={(e) => setCandidateForm({...candidateForm, availability_start: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Salary Expectation (AUD)</label>
                <input
                  type="number"
                  value={candidateForm.salary_expectation}
                  onChange={(e) => setCandidateForm({...candidateForm, salary_expectation: e.target.value})}
                  placeholder="Annual salary expectation"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={candidateForm.sponsorship_needed}
                    onChange={(e) => setCandidateForm({...candidateForm, sponsorship_needed: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Needs Visa Sponsorship</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={candidateForm.rural_experience}
                    onChange={(e) => setCandidateForm({...candidateForm, rural_experience: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Has Rural Experience</span>
                </label>
                
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={candidateForm.housing_needed}
                    onChange={(e) => setCandidateForm({...candidateForm, housing_needed: e.target.checked})}
                    className="mr-2"
                  />
                  <span className="text-sm font-medium text-gray-700">Needs Housing Support</span>
                </label>
              </div>
              
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
                <textarea
                  value={candidateForm.notes}
                  onChange={(e) => setCandidateForm({...candidateForm, notes: e.target.value})}
                  rows="3"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
              </div>
              
              <div className="md:col-span-2">
                <button
                  type="submit"
                  disabled={loading}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {loading ? "Saving..." : (editingCandidate ? "Update Candidate" : "Add Candidate")}
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Candidates List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">Candidate Database</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Experience</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Visa Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Score</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {candidates.map((candidate) => (
                  <tr key={candidate.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{candidate.full_name}</div>
                      <div className="text-sm text-gray-500">{candidate.email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{candidate.location}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {candidate.experience_years} years
                      {candidate.rural_experience && <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Rural</span>}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        candidate.sponsorship_needed 
                          ? 'bg-yellow-100 text-yellow-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {VISA_STATUS_OPTIONS.find(v => v.value === candidate.visa_status)?.label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">{candidate.score.toFixed(1)}/10</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => editCandidate(candidate)}
                        className="text-green-600 hover:text-green-900"
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Application Management Component
  const ApplicationManagement = () => {
    const [showApplicationForm, setShowApplicationForm] = useState(false);
    const [applicationForm, setApplicationForm] = useState({
      job_id: "",
      candidate_id: "",
      cover_letter: ""
    });

    const handleApplicationSubmit = async (e) => {
      e.preventDefault();
      setLoading(true);
      
      try {
        await axios.post(`${API}/applications`, applicationForm);
        await fetchApplications();
        await fetchDashboardStats();
        setShowApplicationForm(false);
        setApplicationForm({
          job_id: "",
          candidate_id: "",
          cover_letter: ""
        });
      } catch (error) {
        console.error("Error creating application:", error);
      } finally {
        setLoading(false);
      }
    };

    const updateApplicationStatus = async (applicationId, status) => {
      try {
        await axios.put(`${API}/applications/${applicationId}`, { status });
        await fetchApplications();
        await fetchDashboardStats();
      } catch (error) {
        console.error("Error updating application status:", error);
      }
    };

    const bulkUpdateApplications = async (status) => {
      if (selectedItems.length === 0) return;
      
      try {
        await axios.post(`${API}/applications/bulk-update`, {
          application_ids: selectedItems,
          status: status
        });
        await fetchApplications();
        await fetchDashboardStats();
        setSelectedItems([]);
      } catch (error) {
        console.error("Error bulk updating applications:", error);
      }
    };

    const getJobTitle = (jobId) => {
      const job = jobs.find(j => j.id === jobId);
      return job ? `${job.title} - ${job.location}` : "Unknown Job";
    };

    const getCandidateName = (candidateId) => {
      const candidate = candidates.find(c => c.id === candidateId);
      return candidate ? candidate.full_name : "Unknown Candidate";
    };

    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center">
          <h2 className="text-3xl font-bold text-gray-800">Application Management</h2>
          <div className="flex space-x-2">
            {selectedItems.length > 0 && (
              <div className="flex space-x-2">
                <button
                  onClick={() => bulkUpdateApplications("screening")}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm"
                >
                  Bulk Move to Screening ({selectedItems.length})
                </button>
                <button
                  onClick={() => bulkUpdateApplications("rejected")}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm"
                >
                  Bulk Reject ({selectedItems.length})
                </button>
              </div>
            )}
            <button
              onClick={() => setShowApplicationForm(!showApplicationForm)}
              className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors"
            >
              {showApplicationForm ? "Cancel" : "Create Application"}
            </button>
          </div>
        </div>

        {showApplicationForm && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4">Create New Application</h3>
            <form onSubmit={handleApplicationSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Job</label>
                <select
                  value={applicationForm.job_id}
                  onChange={(e) => setApplicationForm({...applicationForm, job_id: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  <option value="">Select a job</option>
                  {jobs.map(job => (
                    <option key={job.id} value={job.id}>
                      {job.title} - {job.location}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Candidate</label>
                <select
                  value={applicationForm.candidate_id}
                  onChange={(e) => setApplicationForm({...applicationForm, candidate_id: e.target.value})}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                  required
                >
                  <option value="">Select a candidate</option>
                  {candidates.map(candidate => (
                    <option key={candidate.id} value={candidate.id}>
                      {candidate.full_name} - {candidate.email}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Cover Letter (Optional)</label>
                <textarea
                  value={applicationForm.cover_letter}
                  onChange={(e) => setApplicationForm({...applicationForm, cover_letter: e.target.value})}
                  rows="4"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
              </div>
              
              <button
                type="submit"
                disabled={loading}
                className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                {loading ? "Creating..." : "Create Application"}
              </button>
            </form>
          </div>
        )}

        {/* Applications List */}
        <div className="bg-white rounded-lg shadow-md overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-800">All Applications</h3>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    <input
                      type="checkbox"
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedItems(applications.map(app => app.id));
                        } else {
                          setSelectedItems([]);
                        }
                      }}
                      checked={selectedItems.length === applications.length && applications.length > 0}
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Candidate</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Job</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Applied</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {applications.map((application) => (
                  <tr key={application.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedItems.includes(application.id)}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedItems([...selectedItems, application.id]);
                          } else {
                            setSelectedItems(selectedItems.filter(id => id !== application.id));
                          }
                        }}
                      />
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {getCandidateName(application.candidate_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {getJobTitle(application.job_id)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={application.status}
                        onChange={(e) => updateApplicationStatus(application.id, e.target.value)}
                        className="text-sm border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-2 focus:ring-purple-500"
                      >
                        {APPLICATION_STATUSES.map(status => (
                          <option key={status.value} value={status.value}>{status.label}</option>
                        ))}
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(application.applied_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => updateApplicationStatus(application.id, "interview")}
                        className="text-blue-600 hover:text-blue-900 mr-4"
                      >
                        Interview
                      </button>
                      <button
                        onClick={() => updateApplicationStatus(application.id, "offer")}
                        className="text-green-600 hover:text-green-900"
                      >
                        Offer
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  // Main render
  return (
    <div className="min-h-screen bg-gray-100">
      <Navigation />
      <main className="container mx-auto px-4 py-8">
        {currentView === "dashboard" && <Dashboard />}
        {currentView === "jobs" && <JobManagement />}
        {currentView === "candidates" && <CandidateManagement />}
        {currentView === "applications" && <ApplicationManagement />}
      </main>
    </div>
  );
}

export default App;