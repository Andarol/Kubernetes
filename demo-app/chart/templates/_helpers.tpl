{{- define "simple-app.name" -}}
simple-app
{{- end -}}

{{- define "simple-app.labels" -}}
app.kubernetes.io/managed-by: Helm
{{- end -}}
