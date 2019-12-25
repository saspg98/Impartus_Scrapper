import json
import os
import subprocess
import requests
from multiprocessing.pool import Pool

impartus_base = "http://172.16.3.20/"
impartus_login = impartus_base + "api/auth/signin"
impartus_stream = impartus_base + "api/fetchvideo?ttid={}&token={}&type=index.m3u8"
impartus_lectures = impartus_base + "api/subjects/{}/lectures/{}"

def main():
    username = input("Enter your Impartus username: ")
    password = input("Enter your Impartus password: ")

    payload = {
        "username": username,
        "password": password,
    }

    response = requests.post(impartus_login, data=payload)
    if response.status_code == 200:
        response = json.loads(response.text)
        token = response["token"]  # It's JWT, yay!
    else: 
        print("Invalid username/password. Try again.")
        return

    headers = {"Authorization": "Bearer " + token}

    print("Provide link to course catalog URL")
    print("It'll be off the format: https://a.impartus.com/ilc/#/course/130045/653")
    course_catalog_url = input("Provide link: ")

    # Breakdown the link
    pos = course_catalog_url.find("course")
    pos2 = course_catalog_url.rfind("/")
    subject = course_catalog_url[pos+7:pos2]
    lecture = course_catalog_url[pos2+1:]

    course_lectures_url = impartus_lectures.format(subject, lecture)
    response = requests.get(course_lectures_url, headers=headers)
    if response.ok:
        response = json.loads(response.text)

        # how many worker processes?
        worker_processes = input("How many worker processes you want to use? (Default: 2)")
        if not worker_processes: 
            worker_processes = 2
        else:
            worker_processes = int(worker_processes)
            
        # Create the directory
        title = response[0]["subjectName"]
        working_dir = os.path.join(os.getcwd(), title)
        if not os.path.isdir(working_dir):
            os.makedirs(working_dir)    

        # Modify the number of worker processes and see if you get better performance, I don't :(
        with Pool(worker_processes) as pool:  
            for lecture in response[::-1]:  # Download lecture #1 first
                ttid = lecture["ttid"]
                lec_no = lecture["seqNo"]
                title = lecture["topic"]
                file_name = "{}. {}.mkv".format(lec_no, title)
                url_to_stream = impartus_stream.format(ttid, token)
                pool.apply_async(download_stream, [url_to_stream, os.path.join(working_dir, file_name)])

            pool.close()
            pool.join()
        
            
        
def download_stream(url_to_stream, output_file):
    subprocess.call(["ffmpeg", "-y", "-i", url_to_stream, output_file])

if __name__ == "__main__":
    main()