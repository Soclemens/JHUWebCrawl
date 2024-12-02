# JHUWebCrawl
JHU Webcrawler Group project for EN.695.723.81.FA24

Program setup:
1. Using python version 3.9.5
2. Change to the project directory
3. To enter virtual env, run: $ .\crawler_env\Scripts\activate
4. To set up the dependencies, run: $ pip install -e .
5. To run the program (root directory): $ python -m src.crawler.crawler

# Web Crawler with Distributed Task Management

## Overview

This project is a distributed web crawler designed to fetch and analyze web pages for specific content relevance. It uses the following technologies:

- **Erlang for Windows**: A requirement for running RabbitMQ.
- **RabbitMQ 5.4.0**: A message broker used by Celery to manage distributed task queues.
- **Celery**: A task queue system to distribute crawling tasks.
- **SQLite**: A lightweight database backend for Celery to store task results.
- **Python**: Implements the core crawling logic, task management, and analysis.

## Features

- Distributed task management with Celery and RabbitMQ.
- Concurrent crawling of web pages using `multiprocessing.Pool` and thread pools.
- Relevance calculation based on keyword occurrence.
- Recursively explores URLs up to a specified depth.
- Generates a CSV report summarizing crawled data.
- Graceful shutdown of tasks and workers.

---

## Prerequisites

1. **Install Erlang for Windows**:
   - Download and install from [Erlang's official site](https://www.erlang.org/downloads).

2. **Install RabbitMQ**:
   - Download RabbitMQ 5.4.0 from [RabbitMQ's official site](https://www.rabbitmq.com/download.html).
   - Ensure RabbitMQ is running on your machine.

3. **Python Environment**:
   - Install Python 3.9 or higher.

4. **Install Dependencies**:
   ```bash
   pip install distributed_pyproject.toml


## Run the Crawler

1. To run the program (root direcotry)$ py -m src.crawler.distributed_crawler