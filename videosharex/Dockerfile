FROM python:3.7

# Create project directory (workdir)
RUN mkdir /app
WORKDIR /app
COPY ./* /app/
RUN pip install pipenv
COPY ./Pipfile* /app/
RUN pipenv install --dev
#ENV PORT 8000
#RUN pipenv shell

# Add the remaining source code files to WORKDIR
COPY . .
ENTRYPOINT ["pipenv"]
CMD ["run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
