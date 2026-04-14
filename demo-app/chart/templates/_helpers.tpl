{{- define "demo-app.name" -}}
demo-app
{{- end -}}

{{- define "demo-app.labels" -}}
app.kubernetes.io/managed-by: Helm
{{- end -}}
