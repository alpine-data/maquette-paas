FROM busybox:1.35

# External Port, might be overriden
ENV PORT 3000

# External Port
EXPOSE 3000

# Create a non-root user to own the files and run our server
RUN adduser -D static
USER static
WORKDIR /home/static

# Copy the static website
# Use the .dockerignore file to control what ends up inside the image!
COPY . .

# Run BusyBox httpd
CMD ["sh", "-c", "busybox httpd -f -v -p $PORT"]