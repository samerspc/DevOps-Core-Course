package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"runtime"
	"time"
)

// Application start time for uptime calculation
var startTime = time.Now()

// ServiceInfo represents the complete service information response
type ServiceInfo struct {
	Service  ServiceInfoDetail `json:"service"`
	System   SystemInfo        `json:"system"`
	Runtime  RuntimeInfo       `json:"runtime"`
	Request  RequestInfo       `json:"request"`
	Endpoints []EndpointInfo   `json:"endpoints"`
}

// ServiceInfoDetail contains service metadata
type ServiceInfoDetail struct {
	Name        string `json:"name"`
	Version     string `json:"version"`
	Description string `json:"description"`
	Framework   string `json:"framework"`
}

// SystemInfo contains system information
type SystemInfo struct {
	Hostname        string `json:"hostname"`
	Platform        string `json:"platform"`
	PlatformVersion string `json:"platform_version"`
	Architecture    string `json:"architecture"`
	CPUCount        int    `json:"cpu_count"`
	GoVersion       string `json:"go_version"`
}

// RuntimeInfo contains runtime statistics
type RuntimeInfo struct {
	UptimeSeconds int    `json:"uptime_seconds"`
	UptimeHuman   string `json:"uptime_human"`
	CurrentTime   string `json:"current_time"`
	Timezone      string `json:"timezone"`
}

// RequestInfo contains request metadata
type RequestInfo struct {
	ClientIP  string `json:"client_ip"`
	UserAgent string `json:"user_agent"`
	Method    string `json:"method"`
	Path      string `json:"path"`
}

// EndpointInfo describes available endpoints
type EndpointInfo struct {
	Path        string `json:"path"`
	Method      string `json:"method"`
	Description string `json:"description"`
}

// HealthResponse represents the health check response
type HealthResponse struct {
	Status       string `json:"status"`
	Timestamp    string `json:"timestamp"`
	UptimeSeconds int   `json:"uptime_seconds"`
}

// getSystemInfo collects system information
func getSystemInfo() SystemInfo {
	hostname, _ := os.Hostname()
	if hostname == "" {
		hostname = "unknown"
	}

	return SystemInfo{
		Hostname:        hostname,
		Platform:        runtime.GOOS,
		PlatformVersion: fmt.Sprintf("%s %s", runtime.GOOS, runtime.GOARCH),
		Architecture:    runtime.GOARCH,
		CPUCount:        runtime.NumCPU(),
		GoVersion:       runtime.Version(),
	}
}

// getUptime calculates application uptime
func getUptime() (int, string) {
	delta := time.Since(startTime)
	seconds := int(delta.Seconds())
	
	hours := seconds / 3600
	minutes := (seconds % 3600) / 60
	secs := seconds % 60

	var uptimeHuman string
	if hours > 0 {
		uptimeHuman = fmt.Sprintf("%d hour", hours)
		if hours != 1 {
			uptimeHuman += "s"
		}
	}
	if minutes > 0 {
		if uptimeHuman != "" {
			uptimeHuman += ", "
		}
		uptimeHuman += fmt.Sprintf("%d minute", minutes)
		if minutes != 1 {
			uptimeHuman += "s"
		}
	}
	if seconds < 60 {
		uptimeHuman = fmt.Sprintf("%d second", secs)
		if secs != 1 {
			uptimeHuman += "s"
		}
	}
	if uptimeHuman == "" {
		uptimeHuman = "0 seconds"
	}

	return seconds, uptimeHuman
}

// getRequestInfo extracts request information
func getRequestInfo(r *http.Request) RequestInfo {
	clientIP := r.RemoteAddr
	if forwarded := r.Header.Get("X-Forwarded-For"); forwarded != "" {
		clientIP = forwarded
	}
	if clientIP == "" {
		clientIP = "unknown"
	}

	userAgent := r.Header.Get("User-Agent")
	if userAgent == "" {
		userAgent = "unknown"
	}

	return RequestInfo{
		ClientIP:  clientIP,
		UserAgent: userAgent,
		Method:    r.Method,
		Path:      r.URL.Path,
	}
}

// mainHandler handles the main endpoint
func mainHandler(w http.ResponseWriter, r *http.Request) {
	log.Printf("Request: %s %s from %s", r.Method, r.URL.Path, r.RemoteAddr)

	uptimeSeconds, uptimeHuman := getUptime()
	systemInfo := getSystemInfo()
	requestInfo := getRequestInfo(r)

	info := ServiceInfo{
		Service: ServiceInfoDetail{
			Name:        "devops-info-service",
			Version:     "1.0.0",
			Description: "DevOps course info service",
			Framework:   "Go",
		},
		System: systemInfo,
		Runtime: RuntimeInfo{
			UptimeSeconds: uptimeSeconds,
			UptimeHuman:   uptimeHuman,
			CurrentTime:   time.Now().UTC().Format(time.RFC3339Nano),
			Timezone:      "UTC",
		},
		Request: requestInfo,
		Endpoints: []EndpointInfo{
			{Path: "/", Method: "GET", Description: "Service information"},
			{Path: "/health", Method: "GET", Description: "Health check"},
		},
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(info); err != nil {
		log.Printf("Error encoding JSON: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}

// healthHandler handles the health check endpoint
func healthHandler(w http.ResponseWriter, r *http.Request) {
	uptimeSeconds, _ := getUptime()

	response := HealthResponse{
		Status:       "healthy",
		Timestamp:    time.Now().UTC().Format(time.RFC3339Nano),
		UptimeSeconds: uptimeSeconds,
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(response); err != nil {
		log.Printf("Error encoding JSON: %v", err)
		http.Error(w, "Internal Server Error", http.StatusInternalServerError)
	}
}

// notFoundHandler handles 404 errors
func notFoundHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusNotFound)
	json.NewEncoder(w).Encode(map[string]string{
		"error":   "Not Found",
		"message": "Endpoint does not exist",
	})
}

func main() {
	// Get port from environment variable, default to 8080
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	// Get host from environment variable, default to 0.0.0.0
	host := os.Getenv("HOST")
	if host == "" {
		host = "0.0.0.0"
	}

	// Register handlers
	http.HandleFunc("/", mainHandler)
	http.HandleFunc("/health", healthHandler)

	// Custom 404 handler
	http.HandleFunc("/favicon.ico", notFoundHandler)

	address := fmt.Sprintf("%s:%s", host, port)
	log.Printf("Starting DevOps Info Service...")
	log.Printf("Listening on %s", address)

	if err := http.ListenAndServe(address, nil); err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}
