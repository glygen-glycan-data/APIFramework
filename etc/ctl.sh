#!/bin/bash

SERVICE=`basename $0`
CFGFILE="${SERVICE}.cfg"
CIDFILE="${SERVICE}.cid"
LOGFILE="${SERVICE}.log"
. ${CFGFILE}

if [ "${ANALYTICS}" != "" ]; then
  ANALYTICS="--env WEBSERVICE_BASIC_GOOGLE_ANALYTICS_TAG_ID=${ANALYTICS}"
fi

pull() {
        touch "${LOGFILE}"
	echo -n "Pulling ${IMAGE}: "
	docker pull "${IMAGE}" >> "${LOGFILE}" 2>&1
}

rotate() {
  FILE="$1"
  MAXN=${2:-9}
  if [ -f "$FILE.$MAXN" ]; then
    rm -f "$FILE.$MAXN"
  fi
  N1="$MAXN"
  N0=`expr $N1 - 1`
  while [ $N0 -ge 1 ]; do
    if [ -f "$FILE.$N0" ]; then
      mv -f "$FILE.$N0" "$FILE.$N1"
    fi
    N1="$N0"
    N0=`expr $N1 - 1`
  done
  if [ -f "$FILE" ]; then
    mv -f "$FILE" "${FILE}.1"
  fi
}

start() {
        rotate "${LOGFILE}"
        touch "${LOGFILE}"
	echo -n "Starting ${SERVICE}: "
	USER="`id -u`:`id -g`"
	docker pull "${IMAGE}" >> "${LOGFILE}" 2>&1
        rm -f "${CIDFILE}"
	docker run --cidfile "${CIDFILE}" \
                   --env WEBSERVICE_BASIC_PORT=${PORT} \
                   --env WEBSERVICE_BASIC_MAX_CPU_CORE=${WORKERS:-1} \
                   --name ${NAME:-${SERVICE}} \
                   ${ANALYTICS} \
                   ${EXTRA_ARGS} \
                   -u "${USER}" \
                   -p "${PORT}:${PORT}" \
                   "${IMAGE}" >> ${LOGFILE} 2>&1 &
	sleep 5
	echo `cat ${CIDFILE}`
}

stop() {
	echo -n "Shutting down ${SERVICE}: "
	docker rm -f `cat "${CIDFILE}"` && rm -f "${CIDFILE}"
}

status() {
	docker ps | fgrep -w "${NAME:-${SERVICE}}"
}

stats() {
	docker stats `cat ${CIDFILE}`
}

case "$1" in
    start)
        pull
	start
	status
	;;
    stop)
	stop
	;;
    restart)
        pull
	stop
	start
	status
	;;
    status)
	status
	;;
    stats)
	stats
	;;
    *)
	echo "Usage: $SERVICE {start|stop|restart|status|stats}"
	exit 1
	;;
esac
exit $RETVAL
