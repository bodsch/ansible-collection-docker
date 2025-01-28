#!/usr/bin/env bash

FACTS_FILE="/etc/ansible/facts.d/update_container.fact"

if [ -f "${FACTS_FILE}" ]
then

  data=$(bash "${FACTS_FILE}")

  recreate=$(echo "${data}" | jq -r '.update_needed[] | select(.recreate)')

  # image=$(echo "${recreate}" | jq -r '.image')
  names=$(echo "${recreate}"  | jq -r '.name')

  if [ -n "${names}" ]
  then
    echo ""
    echo "special update hook for:"

    for n in ${names}
    do
      echo "  - ${n}"

      if [ "${n}" = "busybox-2" ]
      then
        echo "cat environments:"
        if [ -f "/opt/container/${n}/container.env" ]
        then
          cat "/opt/container/${n}/container.env"
        fi
      fi
    done
  fi


fi
