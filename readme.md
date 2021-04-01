#### Summary
The newsroom of my country's largest newspaper needs to process the election data in real-time. The electronic election model has a count of + 200 million votes in a few hours. The first media company that processes and displays the election result wins.

It will be necessary to read in real-time the data available by the government during the counting of mayor/councillors elections with +5000 cities and 250 million inhabitants. With update rates ranging from ten seconds to one minute for different data sessions, the system must be able to serve JSON for different pages and applications in real-time for +-200,000 clients connected simultaneously.

The files assembled by the government contain raw and unified data weighing +-4MB, so operation is split the file into small parts to be accessed via the web browser in a granular way.

#### Problem
The previous version developed using java, which downloads large files, applied the parser and save in different tables in a relational database.
This approach generated incalculable databases locks and records duplications. Another parallel process selects from the database using several joins, to creates a granular JSON as a filesystem to drop into the company's FTP to becomes available as a static CDN. 

#### Solution:
* Removed the relational database from the process, including REDIS to be the storage as a high IOPF concurrency.
* Eliminated the competition that sends thousands of archives via FTP, serving the files directly from a lighthttp scalable solution.
* Used Celery to process the background data asynchronously and not concurrency with the application servers.
* ClouldFront configuration in front of the request to decrease the live requests per seconds rate (isn´t included in this example) retaining more than 50% of the traffic.
* It was tried to use put_object for S3, but the latency of boto3 was not as performant as Redis.MSET for uploading thousands of small files simultaneously.

![arch](https://user-images.githubusercontent.com/1752695/113294499-6ecfdf80-92cd-11eb-8264-d1d80f5e4965.jpg)


#### Repository architecture:
I developed some microservices to spread the responsibility for this functionality. The Github repository version is just a simplified variation of the original solution, which uses a much larger data complexity.

**task.py** Celery tasks being performed every 10 seconds reading the information from the file sent from the government (2MB) and slicing them into + -5000 dictionaries on REDIS. Another task running each minute to enrich the Redis with the session data released by the government on a different regularly time basis.

** web.py ** Flask app behind CloudFront configured to keep the same version of the file for {cache-control: max-age 10}. When the request reaches the route/view the data is waiting in a high available REDIS key/value entry. 
#####Gunicorn offer a nice performance otimization and helps a lot to serve 10.000 requests in parallel:
    
The web application doesn't have any processing, together with the amazing gunicorn fine-tune, each large AWS instance can serve thousands of connections simultaneous.
    

#### Try yourself:
Install REDIS as your taste, replace the URL into the .env file, then:
    
    docker-compose build
    docker-compose up
    curl http://127.0.0.1:5020/cities/mayors-sp-sao-paulo.json

Checkout github code project:
[https://github.com/avictorino/realtime_elections](https://github.com/avictorino/realtime_elections)
 
