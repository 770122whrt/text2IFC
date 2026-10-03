FROM text2ifc/repair-tools:py312-ifc085
USER 0:0
RUN /opt/venv/bin/python -m pip install --disable-pip-version-check \
    openai==2.43.0 jsonschema==4.26.0 lxml==5.4.0 shapely==2.1.2 ifcdiff==0.8.5 \
    && /opt/venv/bin/python -m pip check
ENV PATH="/opt/venv/bin:${PATH}"
USER 10001:10001
WORKDIR /workspace
