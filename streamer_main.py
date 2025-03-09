import cv2
import gi
import numpy as np

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib


Gst.init(None)


def create_pipeline(rtsp_url):
    pipeline_description = f"""
            rtspsrc location={rtsp_url} latency=0 !
            rtph264depay !
            avdec_h264 !
            videoconvert !
            video/x-raw,format=BGR !
            appsink name=appsink emit-signals=true
        """
    pipeline = Gst.parse_launch(pipeline_description)

    return pipeline


def get_frame(sample):
    caps = sample.get_caps()
    structure = caps.get_structure(0)
    width = structure.get_value("width")
    height = structure.get_value("height")

    buffer = sample.get_buffer()
    success, map_info = buffer.map(Gst.MapFlags.READ)
    if not success:
        return Gst.FlowReturn.ERROR
    buffer.unmap(map_info)

    frame = np.frombuffer(map_info.data, dtype=np.uint8)
    frame = frame.reshape((height, width, 3))  # Размер кадра должен соответствовать RTSP-потоку
    frame = cv2.resize(frame, (1280, 720))

    return frame


def process_frame(frame):

    # Получаем данные от детектора, отдаем трекеру и получаем bb

    # Пример bounding box (координаты: x1, y1, x2, y2)
    boxes = [(50, 50, 200, 200), (300, 100, 400, 300)]

    for (x1, y1, x2, y2) in boxes:
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

    return frame


def video_streaming(rtsp_url):
    pipeline = create_pipeline(rtsp_url)
    sink = pipeline.get_by_name("appsink")
    pipeline.set_state(Gst.State.PLAYING)

    bus = pipeline.get_bus()
    bus.add_signal_watch()

    loop = GLib.MainLoop()

    try:
        while True:
            sample = sink.emit("pull-sample")
            if sample:
                frame = get_frame(sample)

                processed_frame = process_frame(frame)

                cv2.imshow("RTSP Stream with Bounding Boxes", processed_frame)
                cv2.waitKey(1)

            else:
                break

    except KeyboardInterrupt:
        print("Interrupted by user")

    finally:
        pipeline.set_state(Gst.State.NULL)
        cv2.destroyAllWindows()


def main():
    rtsp_url = "necessary_rtsp_url"
    video_streaming(rtsp_url)


if __name__ == "__main__":
    main()
