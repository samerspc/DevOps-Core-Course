{{/*
Expand the name of the chart.
*/}}
{{- define "app-python.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "app-python.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{/*
Chart version label
*/}}
{{- define "app-python.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "app-python.labels" -}}
helm.sh/chart: {{ include "app-python.chart" . }}
{{ include "app-python.selectorLabels" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "app-python.selectorLabels" -}}
app.kubernetes.io/name: {{ include "app-python.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Kubernetes Secret resource name (Helm-managed credentials).
*/}}
{{- define "app-python.secretName" -}}
{{- printf "%s-secret" (include "app-python.fullname" .) }}
{{- end }}

{{/*
ServiceAccount name for the workload (Vault K8s auth binds to this SA).
*/}}
{{- define "app-python.serviceAccountName" -}}
{{- if .Values.serviceAccount.name }}
{{- .Values.serviceAccount.name }}
{{- else }}
{{- include "app-python.fullname" . }}
{{- end }}
{{- end }}

{{/*
Non-sensitive env vars (DRY — used from deployment; extend in one place).
*/}}
{{- define "app-python.standardEnv" -}}
- name: APP_CHART_NAME
  value: {{ include "app-python.name" . | quote }}
- name: HELM_RELEASE
  value: {{ .Release.Name | quote }}
- name: VISITS_FILE
  value: "/data/visits"
- name: APP_CONFIG_PATH
  value: "/config/config.json"
{{- end }}

{{/*
Merged pod annotations: user podAnnotations + optional Vault Agent Injector.
*/}}
{{- define "app-python.podAnnotations" -}}
{{- $ann := dict }}
{{- range $k, $v := (default (dict) .Values.podAnnotations) }}
{{- $_ := set $ann $k $v }}
{{- end }}
{{- if .Values.vault.inject.enabled }}
{{- $_ := set $ann "vault.hashicorp.com/agent-inject" "true" }}
{{- $_ := set $ann "vault.hashicorp.com/role" .Values.vault.role }}
{{- if .Values.vault.inject.template.enabled }}
{{- $_ := set $ann "vault.hashicorp.com/agent-inject-secret-config" .Values.vault.inject.secretPath }}
{{- $_ := set $ann "vault.hashicorp.com/agent-inject-template-config" .Values.vault.inject.template.content }}
{{- else if .Values.vault.inject.secretPath }}
{{- $_ := set $ann "vault.hashicorp.com/agent-inject-secret-config" .Values.vault.inject.secretPath }}
{{- end }}
{{- end }}
{{- if and .Values.configMap.enabled .Values.configReload.checksumAnnotation }}
{{- $sum := printf "%s|%s|%s" (.Files.Get "files/config.json") .Values.environment .Values.logLevel | sha256sum }}
{{- $_ := set $ann "checksum/config" $sum }}
{{- end }}
{{- toYaml $ann }}
{{- end }}
