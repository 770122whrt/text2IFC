# Optional B property runtime. No project data, model weights, or credentials.
FROM text2ifc/repair-tools:py312-ifc085-v2
USER 0:0
RUN python -m pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.9.0
RUN python -m pip install --no-cache-dir --index-url https://pypi.org/simple qdrant-client==1.18.0 sentence-transformers==5.6.1 transformers==5.14.1
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1 OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false
USER 65532:65532
