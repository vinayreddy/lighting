#!/usr/bin/env python

from pyunifiprotect import ProtectApiClient
from pyunifiprotect.data import SmartDetectObjectType
from getpass import getpass
import datetime
import os
import pytz
import openai
from tqdm import tqdm



# Replace the placeholders with your actual information
UNIFI_PROTECT_IP = "192.168.1.1"
port = "443"
USERNAME = "@gmail.com"
PASSWORD = getpass("Enter your password: ")


# Create an instance of the ProtectApiClient class
unifi_server = ProtectApiClient(UNIFI_PROTECT_IP,  port, USERNAME,PASSWORD, verify_ssl=False)
#%%
await unifi_server.update() # this will initialize the protect .bootstrap and open a Websocket connection for updates

#%%

# Fetch cameras and print their names and IDs

for camera in unifi_server.bootstrap.cameras.values():
	print(f"Camera Name: {camera.name} | Camera ID: {camera.id}")

#%%
async def process_unifi_videos(
		start_time,
		end_time,
		cameras,
		unifi_server,
		filter_by_person=True,
		filter_by_kids=True,
		output_log=False,
		transcription=False,
		continuous=False
		):

	all_events = []
		consolidated_events = []
		class Event:
			def __init__(self, camera, start, end):
				self.camera = camera
						self.start = start
						self.end = end


		def filter_persons(cameras, all_events):
			person_filtered_events = [event for event in all_events if SmartDetectObjectType.PERSON in event.smart_detect_types]

				if '641bae9002b0ff03e4005875' in [camera.id for camera in cameras]:
					g3_filtered_events = [event for event in all_events if (event.camera.id == '641bae9002b0ff03e4005875')]
						person_filtered_events += g3_filtered_events
				return person_filtered_events



		def convert_to_pacific(utc_time):
			pacific = pytz.timezone('America/Los_Angeles')
				return utc_time.astimezone(pacific)

		def filter_for_kids_schedule(person_filtered_events, convert_to_pacific):
			return [
					event
					for event in person_filtered_events
					if not (
						(
							convert_to_pacific(event.start).weekday() == 6
							and convert_to_pacific(event.start).time()
							> datetime.time(18, 1)
							)  # Sundays after 5:15 PM
						or (
							convert_to_pacific(event.start).weekday() == 2
							)  # All Wednesdays
						or (
							convert_to_pacific(event.start).weekday() == 3
							and convert_to_pacific(event.start).time()
							< datetime.time(11, 0)
							)  # Thursdays before 11 AM
						or (
							convert_to_pacific(event.start).weekday() == 4
							and convert_to_pacific(event.start).time()
							> datetime.time(8, 45)
							)  # Fridays after 8:45 AM
						or (
							convert_to_pacific(event.start).weekday() == 5
							and convert_to_pacific(event.start).time()
							< datetime.time(17, 0)
							)  # Saturdays before 5 PM
						or (
							convert_to_pacific(event.start).weekday() == 0
							and convert_to_pacific(event.start).time()
							< datetime.time(17, 30)
							)  # Mondays before 5:30 PM
						or (
							convert_to_pacific(event.start).weekday() == 1
							and (
								datetime.time(10, 35)
								<= convert_to_pacific(event.start).time()
								<= datetime.time(16, 30)
								or convert_to_pacific(event.start).time()
								> datetime.time(18, 35)
								)
							)  # Tuesdays between 10:35 AM and 4:30 PM or after 6:35 PM
						)
					]

		if not continuous:
			all_events = await unifi_server.get_events(
					start=start_time,
					end=end_time,)

			if filter_by_person:
				all_events = filter_persons(cameras, all_events)

				if filter_by_kids:
					all_events = filter_for_kids_schedule(all_events, convert_to_pacific)
		else:
			# In case of continuous mode, set all_events to a continuous block for each camera
				for camera in cameras:
					continuous_event = Event(camera=camera, start=start_time, end=end_time)  # Assuming Event class has these properties, modify accordingly
						all_events.append(continuous_event)





		async def get_event_data(unifi_server, camera_id, start, end, output_log):
			video = await unifi_server.get_camera_video(camera_id, start, end)
				if output_log:
					event_log = await unifi_server.get_events(start=start, end=end)
						event_log = [logged_event for logged_event in event_log if logged_event.camera.id == camera_id]
						return video, event_log
				else:
					return video, None



		def save_event_data(camera, start, end, video, log):
			local_start = convert_to_pacific(start)
				local_end = convert_to_pacific(end)
				with open(f"{camera.name} {local_start.strftime('%m-%d-%Y, %H.%M.%S')} - {local_end.strftime('%m-%d-%Y, %H.%M.%S')}.mp4", "wb") as f:
					f.write(video)
				if log:
					with open(f"{camera.name} {local_start.strftime('%m-%d-%Y, %H.%M.%S')} - {local_end.strftime('%m-%d-%Y, %H.%M.%S')}_log.txt", "w") as f:
						f.write(str(log))



		for camera in cameras:
			camera_events = [event for event in all_events if event.camera.id == camera.id]
				for event in camera_events:
					if convert_to_pacific(event.start)< start_time:
						#increase the start time to start_times[0] after accounting for their different timezones
								time_difference = start_time - convert_to_pacific(event.start)
								event.start += time_difference
								#update camera_events to reflect the new start time
						if not consolidated_events:
							consolidated_events.append(event)
						else:
							last_event = consolidated_events[-1]
								#check if they are within 2 minutes and also if they are the same camera
								if (event.start - last_event.end <= datetime.timedelta(minutes=2) and event.camera.id == last_event.camera.id):
									consolidated_events[-1].end = event.end
								else:
									consolidated_events.append(event)

		#drop all consolidated_events shorter than 5 seconds
		consolidated_events = [event for event in consolidated_events if event.end - event.start > datetime.timedelta(seconds=5)]

		for event in tqdm(consolidated_events, desc="Processing Events", unit="event"):
			# If event/video is longer than 80 minutes, split it up
				while (event.end - event.start).total_seconds() > 4800:
					video, log = await get_event_data(unifi_server, event.camera.id, event.start, event.start + datetime.timedelta(minutes=80), output_log)
						save_event_data(event.camera, event.start, event.start + datetime.timedelta(minutes=80), video, log)
						event.start += datetime.timedelta(minutes=80)
				video, log = await get_event_data(unifi_server, event.camera.id, event.start, event.end, output_log)
				save_event_data(event.camera, event.start, event.end, video, log)





#%%

###inputs & config
#takes only one time at a time to keep it simple
start_time = datetime.datetime(2024, 6, 20, 17,25, 0, tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))
end_time = datetime.datetime(2024, 6, 20, 20,5,0, tzinfo=datetime.timezone(datetime.timedelta(hours=-7)))

folder = '/Users/mp/Library/A1'

cameras = [unifi_server.bootstrap.cameras["6400644b02b0ea03e4000a70"], #"Crystal Cam"
					 unifi_server.bootstrap.cameras["640066260299ea03e4000a9a"],#, #G4 instant in Garage
					 unifi_server.bootstrap.cameras["641bae9002b0ff03e4005875"], #G3 instant on stairs
					 unifi_server.bootstrap.cameras["64c3dd3600a57d03e4004148"], #AI Theta outside front door
					 unifi_server.bootstrap.cameras["6559802301373303e4033b4e"]] #G5 Flex at side door


os.chdir(folder)


await process_unifi_videos(start_time, end_time, cameras, unifi_server, filter_by_person=True, filter_by_kids=False, output_log=False, transcription=False, continuous=False)
# %%
