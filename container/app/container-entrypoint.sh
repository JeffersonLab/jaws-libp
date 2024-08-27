#!/bin/bash

beginswith() { case $2 in "$1"*) true;; *) false;; esac; }

# Set Timezone
export TZ="/usr/share/zoneinfo/$TZ"

echo "-------------------------------------------------------"
echo "Step 1: Waiting for Schema Registry to start listening "
echo "-------------------------------------------------------"
while [ $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) -eq 000 ] ; do
  echo -e $(date) " Registry listener HTTP state: " $(curl -s -o /dev/null -w %{http_code} http://registry:8081/schemas/types) " (waiting for 200)"
  sleep 5
done


echo "------------------------"
echo "Step 2: Creating Topics "
echo "------------------------"
create_topics


echo "---------------------------------------"
echo "Step 3: Adding Schemas to the registry "
echo "---------------------------------------"
create_schemas


echo "-------------------------"
echo "Step 4: Adding locations "
echo "-------------------------"
if [[ -z "${ALARM_LOCATIONS}" ]]; then
  echo "No locations specified"
elif beginswith 'https://' "${ALARM_LOCATIONS}"; then
  echo "HTTPS URL specified: $ALARM_LOCATIONS"
  wget -O /tmp/locations "$ALARM_LOCATIONS"
  set_location --file /tmp/locations
elif [[ -f "$ALARM_LOCATIONS" ]]; then
  echo "Attempting to setup locations from file $ALARM_LOCATIONS"
  set_location --file "$ALARM_LOCATIONS"
else
  echo "Attempting to setup locations"
  IFS=','
  read -a definitions <<< "$ALARM_LOCATIONS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      parent="${def[1]}"

      PARMS=("${name}")

      if [[  ! -z "${parent}" ]]; then
        PARMS+=(--parent "${parent}")
      fi

      set_location "${PARMS[@]}"
    done
fi


echo "--------------------------"
echo "Step 5: Adding systems "
echo "--------------------------"
if [[ -z "${ALARM_SYSTEMS}" ]]; then
  echo "No systems specified"
elif beginswith 'https://' "${ALARM_SYSTEMS}"; then
  echo "HTTPS URL specified: $ALARM_SYSTEMS"
  wget -O /tmp/systems "$ALARM_SYSTEMS"
  set_category --file /tmp/systems
elif [[ -f "$ALARM_SYSTEMS" ]]; then
  echo "Attempting to setup systems from file $ALARM_SYSTEMS"
  set_category --file "$ALARM_SYSTEMS"
else
  echo "Attempting to setup categories"
  IFS=','
  read -a definitions <<< "$ALARM_SYSTEMS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      team="${def[1]}"

      PARMS=("${name}")

      if [[  ! -z "${team}" ]]; then
        PARMS+=(--team "${team}")
      fi

      set_category "${PARMS[@]}"
    done
fi


echo "-----------------------"
echo "Step 6: Adding actions "
echo "-----------------------"
if [[ -z "${ALARM_ACTIONS}" ]]; then
  echo "No action definitions specified"
elif beginswith 'https://' "${ALARM_ACTIONS}"; then
  echo "HTTPS URL specified: $ALARM_ACTIONS"
  wget -O /tmp/actions "$ALARM_ACTIONS"
  set_action --file /tmp/actions
elif [[ -f "$ALARM_ACTIONS" ]]; then
  echo "Attempting to setup action definitions from file $ALARM_ACTIONS"
  set_action --file "$ALARM_ACTIONS"
else
  echo "Attempting to setup actions"
  IFS=','
  read -a definitions <<< "$ALARM_ACTIONS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      category="${def[1]}"
      priority="${def[2]}"
      rationale="${def[3]}"
      correctiveaction="${def[4]}"
      latchable="${def[5]}"
      filterable="${def[6]}"
      ondelayseconds="${def[7]}"
      offdelayseconds="${def[8]}"

      PARMS=("${name}" --category "${category}" --priority "${priority}" --rationale "${rationale}")
      PARMS+=(--correctiveaction "${correctiveaction}")

      if [[ "${latchable}" == "True" ]]; then
        PARMS+=(--latchable)
      else
        PARMS+=(--not-latchable)
      fi

      if [[ "${filterable}" == "True" ]]; then
        PARMS+=(--filterable)
      else
        PARMS+=(--not-filterable)
      fi

      if [[  ! -z "${ondelayseconds}" ]]; then
        PARMS+=(--ondelayseconds ${ondelayseconds})
      fi

      if [[  ! -z "${offdelayseconds}" ]]; then
        PARMS+=(--offdelayseconds ${offdelayseconds})
      fi

      set_class "${PARMS[@]}"
    done
fi


echo "--------------------------------------------"
echo "Step 7: Adding alarm registration instances "
echo "--------------------------------------------"
if [[ -z "${ALARMS}" ]]; then
  echo "No alarm definitions specified"
elif beginswith 'https://' "${ALARMS}"; then
  echo "HTTPS URL specified: $ALARMS"

  if [[ -n "${ALARMS_URL_CSV}" ]]; then
    echo "Using URL_CSV: $ALARMS_URL_CSV"
    IFS=','
    read -a definitions <<< "$ALARMS_URL_CSV"
    for defStr in "${definitions[@]}";
      do
        echo "Loading URL: ${ALARMS}/${defStr}"
        wget -O /tmp/alarms "${ALARMS}/${defStr}"
        set_instance --file /tmp/alarms
      done
  else
    echo "Grabbing single URL"
    wget -O /tmp/alarms "$ALARMS"
    set_instance --file /tmp/alarms
  fi
elif [[ -f "$ALARMS" ]]; then
  echo "Attempting to setup alarm definitions from file $ALARMS"
  set_instance --file "$ALARMS"
else
  echo "Attempting to setup instances"
  IFS=','
  read -a definitions <<< "$ALARMS"
  for defStr in "${definitions[@]}";
    do
      IFS='|'
      read -a def <<< "$defStr"
      name="${def[0]}"
      action="${def[1]}"
      pv="${def[2]}"
      location="${def[3]}"
      managedby="${def[4]}"
      maskedby="${def[5]}"
      screencommand="${def[6]}"

      PARMS=("${name}" --action "${action}" --location "${location}" --screencommand "${screencommand}")

      if [[ ! -z "${pv}" ]]; then
        PARMS+=(--pv "${pv}")
      fi

      if [[  ! -z "${managedby}" ]]; then
        PARMS+=(--managedby "${managedby}")
      fi

      if [[  ! -z "${maskedby}" ]]; then
        PARMS+=(--maskedby "${maskedby}")
      fi

      set_instance "${PARMS[@]}"
    done
fi

echo "-------------------------"
echo "Step 8: Adding overrides "
echo "-------------------------"
if [[ -z "${ALARM_OVERRIDES}" ]]; then
  echo "No override definitions specified"
elif beginswith 'https://' "${ALARM_OVERRIDES}"; then
  echo "HTTPS URL specified: $ALARM_OVERRIDES"
  wget -O /tmp/overrides "$ALARM_OVERRIDES"
  set_override --file /tmp/overrides
elif [[ -f "$ALARM_OVERRIDES" ]]; then
  echo "Attempting to setup class definitions from file $ALARM_OVERRIDES"
  set_override --file "$ALARM_OVERRIDES"
else
  echo "Non-file overrides from env not supported!"
fi

echo "---------------------"
echo "Step 9: Initialized! "
echo "---------------------"
touch /home/jaws/initialized

sleep infinity
