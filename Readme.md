# Project "questions"

The application accepts a request to receive questions and returns one last question/answer from the previous request. If there have not been any requests yet, {"first_request": "no questions"} is returned.

An endpoint "/questions" is created for the post request. In the request, you need to pass json with number of questions {"questions_num": 2}, then the application accesses to external api to get the "questions_num" number of unique answers. Saves it to the database and returns one response from the previous request

The project always receives specified number of unique responses from a external api. When receiving response already in the database, requests are repeated until all unique responses are received. Then they are added to the database

## clone repository 


    mkdir app

    cd cat app

    git clone https://github.com/se-andrey/questions.git


If there is no docker/docker-compose on the server, install it. Instructions https://docs.docker.com/

### launch
    docker-compose up --build 

### usage example
Response at the first request

<img height="558" src="C:\Users\Андрей\Desktop\тестовые задания\bewise\first request.JPG" title="first request" width="714"/>

Response for the second request returns the last question received from the previous request

<img height="633" src="C:\Users\Андрей\Desktop\тестовые задания\bewise\second request.JPG" title="second request" width="709"/>
