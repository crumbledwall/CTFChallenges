FROM node:14-alpine

ENV BASE_DIR=/var/www

RUN set -ex \
  && yarn global add pm2 \
  && mkdir -p ${BASE_DIR}/web \
  && chown root:root -R ${BASE_DIR} \
  && chmod 0755 -R ${BASE_DIR}

COPY web/ ${BASE_DIR}/web
COPY process.yaml ${BASE_DIR}
COPY flag readflag /

RUN mkdir ${BASE_DIR}/web/sessions \
  && chmod 0777 -R ${BASE_DIR}/web/sessions \
  && chown root:root /flag /readflag \
  && chmod 000 /flag \
  && chmod 4001 /readflag \
  && set -ex \
  && cd ${BASE_DIR}/web \
  && yarn install --production --network-timeout 30000

WORKDIR ${BASE_DIR}
USER node
CMD [ "pm2-docker", "process.yaml" ]
