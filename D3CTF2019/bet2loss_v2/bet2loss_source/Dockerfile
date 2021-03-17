FROM python:3.7
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com
COPY . /code/
CMD [ "gunicorn", "bet2loss.wsgi:application", "-b 0.0.0.0:8000" ,"--workers","10"]
