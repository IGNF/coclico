FROM mambaorg/micromamba:latest as mamba_pdal
COPY environment.yml /environment.yml
USER root
RUN micromamba env create -n coclico -f /environment.yml


FROM debian:bullseye-slim

# install PDAL
COPY --from=mamba_pdal /opt/conda/envs/coclico/bin/pdal /opt/conda/envs/coclico/bin/pdal
COPY --from=mamba_pdal /opt/conda/envs/coclico/bin/python /opt/conda/envs/coclico/bin/python
COPY --from=mamba_pdal /opt/conda/envs/coclico/lib/ /opt/conda/envs/coclico/lib/
COPY --from=mamba_pdal /opt/conda/envs/coclico/ssl /opt/conda/envs/coclico/ssl
COPY --from=mamba_pdal /opt/conda/envs/coclico/share/proj/proj.db /opt/conda/envs/coclico/share/proj/proj.db

ENV PATH=$PATH:/opt/conda/envs/coclico/bin/
ENV PROJ_LIB=/opt/conda/envs/coclico/share/proj/

WORKDIR /coclico
RUN mkdir tmp
COPY coclico coclico
COPY test test
COPY configs configs

# Copy test data that are stored directly in the coclico repository
COPY data/mpap0 data/mpap0
COPY data/mpla0 data/mpla0
COPY data/mobj0 data/mobj0
COPY data/csv data/csv
