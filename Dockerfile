FROM rocker/shiny-verse:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    libcurl4-openssl-dev \
    libssl-dev \
    libxml2-dev \
    libcairo2-dev \
    libxt-dev \
    libssh2-1-dev \
    wget \
    unzip \
    chromium-browser

# Install Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable

# Install ChromeDriver
RUN CHROME_DRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE) \
    && wget -q -O /tmp/chromedriver.zip https://chromedriver.storage.googleapis.com/${CHROME_DRIVER_VERSION}/chromedriver_linux64.zip \
    && unzip /tmp/chromedriver.zip -d /usr/local/bin \
    && rm /tmp/chromedriver.zip \
    && chmod +x /usr/local/bin/chromedriver

# Install R packages as root
RUN R -e "install.packages(c('shiny', 'reticulate', 'ggExtra', 'readr'), repos='https://cloud.r-project.org/')"

# Install development packages from GitHub as root
RUN R -e "install.packages('remotes', repos='https://cloud.r-project.org/'); remotes::install_github(c('rstudio/bslib', 'rstudio/httpuv'))"

# Set up a new user named "user" with user ID 1000
RUN useradd -m -u 1000 user

# Set up the app directory and change ownership
RUN mkdir -p /home/user/app && chown -R user:user /home/user/app

# Switch to the "user" user
USER user

# Set home to the user's home directory
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory to the user's home directory
WORKDIR $HOME/app

# Install Python packages
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir selenium webdriver_manager

# Create a directory for webdriver_manager and set permissions
RUN mkdir -p $HOME/.wdm && chmod 755 $HOME/.wdm

# Copy the application files
COPY --chown=user . $HOME/app

# Expose the port Shiny runs on
EXPOSE 7860

# Set environment variables
ENV CHROMEDRIVER_PATH /usr/local/bin/chromedriver
ENV WDM_LOCAL=1
ENV WDM_PATH=$HOME/.wdm

# Add a health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:7860 || exit 1

CMD ["R", "-e", "shiny::runApp('/home/user/app', host = '0.0.0.0', port = 7860)"]





