FROM ubuntu:20.04

WORKDIR /planner
COPY . /planner

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive TZ=Etc/UTC apt-get -y install tzdata
RUN apt-get -y install git curl gnupg libompl-dev build-essential cmake

RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian all main" | tee /etc/apt/sources.list.d/sbt.list
RUN echo "deb https://repo.scala-sbt.org/scalasbt/debian /" | tee /etc/apt/sources.list.d/sbt_old.list
RUN curl -sL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x2EE0EA64E40A89B84B2DF73499E82A75642AC823" | apt-key add
RUN apt-get update \
  && apt-get -y install git curl sbt

RUN mkdir deps && cd deps \
 &&  curl https://download.java.net/openjdk/jdk12/ri/openjdk-12+32_linux-x64_bin.tar.gz --output java.tar.gz \
 && tar xvf java.tar.gz \
 && rm -f ./java.tar.gz
ENV JAVA_HOME="/planner/deps/jdk-12"
ENV PATH="/planner/deps/jdk-12/bin:${PATH}"

RUN cd deps && git clone https://github.com/FedericoPecora/coordination_oru.git \
 && cd coordination_oru \
 && ./gradlew install \
 && cd SimpleReedsSheppCarPlanner \
 && mkdir build \
 && cd build \
 && cmake .. \
 && make \
 && make install \
 && ldconfig
 
RUN cd deps && git clone https://github.com/uwe-koeckemann/AIDDL.git \
 && cd AIDDL \
 && git checkout develop

RUN cd deps/AIDDL/external/coordination_oru/ && sbt compile publishM2

RUN cd deps && git clone https://github.com/uwe-koeckemann/SpiderPlan.git \
 && cd SpiderPlan/spiderplan && sbt compile publishM2 \
 && cd ../lib/coordination_oru/ && sbt compile publishM2

RUN sbt compile

ENV AIDDL_PATH="/planner/AIDDL/core/aiddl:/planner/AIDDL/common/aiddl"

EXPOSE 8061

CMD [ "sbt", "run" ]
