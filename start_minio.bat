@echo off
echo Starting MinIO server...
docker run -d -p 9000:9000 --name minio -e MINIO_ROOT_USER=admin -e MINIO_ROOT_PASSWORD=password -v minio_data:/data quay.io/minio/minio server /data
echo MinIO started!
pause 