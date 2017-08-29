import csv
import requests

from transitfeed import Agency, FeedInfo, Route, Schedule, ServicePeriod, Stop, Trip


def add_agency(schedule):
    # TODO: fix email field
    tcat = Agency(name='Tompkins Consolidated Area Transit',
                  url='https://tcatbus.com/',
                  timezone='America/New_York',
                  email='tcat@tcatmail.com',
                  agency_phone='(607) 277-RIDE',
                  lang='en')
    schedule.AddAgencyObject(tcat)
    return tcat


def add_stops(schedule):
    stops = []
    stops_response = requests.get('https://realtimetcatbus.availtec.com/InfoPoint/rest/Stops/GetAllStops')
    stops_json = stops_response.json()
    for stop in stops_json:
        stops.append(Stop(name=stop['Name'],
                          stop_id=str(stop['StopId']),
                          lat=stop['Latitude'],
                          lng=stop['Longitude']))
        schedule.AddStopObject(stops[-1])
    return stops


def add_routes(schedule):
    routes = []
    routes_response = requests.get('https://realtimetcatbus.availtec.com/InfoPoint/rest/Routes/GetVisibleRoutes')
    routes_json = routes_response.json()
    # TODO: add color and url by using field_dict
    for route in routes_json:
        routes.append(Route(short_name=str(route['RouteId']),
                            long_name=route['LongName'],
                            route_id=str(route['RouteId']),
                            route_type=3)) # it's a bus
        schedule.AddRouteObject(routes[-1])
    return routes


def add_service_periods(schedule):
    weekdays = ServicePeriod(id='Weekdays')
    weekdays.SetStartDate('20170820')
    weekdays.SetEndDate('20180120')
    weekdays.SetWeekdayService()
    schedule.AddServicePeriodObject(weekdays)

    weekends = ServicePeriod(id='Weekends')
    weekends.SetStartDate('20170820')
    weekends.SetEndDate('20180120')
    weekends.SetWeekendService()
    schedule.AddServicePeriodObject(weekends)


def add_trips(schedule):
    trips = []
    for route in schedule.GetRouteList():
        route_info_response = requests.get('https://realtimetcatbus.availtec.com/InfoPoint/rest/RouteDetails/Get/{}'
                              .format(route.route_id))
        route_info_json = route_info_response.json()

        directions_response = requests.get('https://realtimetcatbus.availtec.com/InfoPoint/rest/RouteDetails/GetDirectionsByRouteId/{}'
                              .format(route.route_id))
        directions_json = directions_response.json()

        for direction in directions_json:
            stop_sequence = [None for _ in range(0, len(route_info_json['RouteStops']))]

            for route_stop in filter(lambda rs : rs['Direction'] == direction['Dir'],
                                     route_info_json['RouteStops']):
                stop_sequence[route_stop['SortOrder'] - 1] = schedule.GetStop(str(route_stop['StopId']))

            direction_id = 0 if direction['Dir'] == 'O' else 1 if direction['Dir'] == 'I' else None

            for service_period in ['Weekdays', 'Weekends']:
                try:
                    with open('times/{}{}{}.txt'
                              .format(route.route_id, direction['Dir'],  service_period),
                              'r') as times_file:
                        times_reader = csv.reader(times_file)
                        timepoints = times_reader.next()

                        for counter, row in enumerate(times_reader):
                            trip = Trip(field_dict={'route_id' : route.route_id,
                                                    'trip_id' : route.route_id
                                                              + direction['Dir']
                                                              + str(counter),
                                                    'service_id' : service_period,
                                                    'headsign' : direction['DirectionDesc'],
                                                    'direction_id' : direction_id})
                            schedule.AddTripObject(trip)

                            next_timepoint = 0
                            for stop in filter(lambda s : s is not None, stop_sequence):
                                if stop.stop_id == timepoints[next_timepoint]:
                                    stop_time = row[next_timepoint]
                                    next_timepoint += 1
                                else:
                                    stop_time = None
                                trip.AddStopTime(stop, stop_time=stop_time)

                            if direction['Dir'] == 'LB':
                                # it's a loop
                                trip.AddStopTime(stop_sequence[0], stop_time=row[-1])

                except Exception as e:
                    pass
    return trips


def add_feed_info(schedule):
    yinnon = FeedInfo(field_dict={'feed_publisher_name' : 'Yinnon Sanders',
                                  'feed_publisher_url'  : 'https://github.com/yinnonsanders',
                                  'feed_lang'           : 'en',
                                  'feed_start_date'     : '20170820',
                                  'feed_end_date'       : '20180120',
                                  'feed_version'        : '0.0.1'})
    schedule.AddFeedInfoObject(yinnon)
    return yinnon


def main():
    schedule = Schedule()
    agency = add_agency(schedule)
    stops = add_stops(schedule)
    routes = add_routes(schedule)
    service_periods = add_service_periods(schedule)
    trips = add_trips(schedule)
    feed_info = add_feed_info(schedule)
    schedule.Validate()
    schedule.WriteGoogleTransitFeed('tcat_gtfs.zip')


if __name__ == '__main__':
    main()
