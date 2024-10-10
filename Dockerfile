# Base layer (default dependencies) to use
# You should find more base layers at https://hub.docker.com

# 사용할 베이스 이미지
FROM python:3.12.4
ENV LC_ALL en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US.UTF-8

# Install expect >>> To press enter
RUN apt-get update && apt-get install -y expect

# Custom location to place code files
RUN mkdir -p /app/
WORKDIR /app/

COPY /config/ /app/config/
# app.py
COPY app.py /app/app.py
# menu.py
COPY menu.py /app/menu.py
# pages
COPY pages/ /app/pages/
# server
COPY server/ /app/server/
# fonts
COPY fonts/ /app/fonts/
# .streamlit
COPY .streamlit /app/.streamlit
# requirements.txt
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir --upgrade pip
RUN pip3 install -r /app/requirements.txt

EXPOSE 8501

# Run aicore configure command
# Copy the script into the container
COPY configure_aicore.exp /app/
# Set the script to be executable
RUN chmod +x /app/configure_aicore.exp
# Run the script
RUN /usr/bin/expect /app/configure_aicore.exp
# fonts 설정 
RUN chmod -R 755 /app/fonts/

# Run your application
CMD ["streamlit","run","app.py"]