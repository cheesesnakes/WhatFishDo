# WhatFishDo: A Behavior Annotation Tool for Videos collected from the field.

## Overview

WhatFishDo is designed to assist researchers in annotating behavior from video footage. The tool supports detection, tracking, and annotation of animals in videos, leveraging YOLO for detection and OpenCV for tracking. It also supports GPU acceleration for faster processing.

## Features

- **Detection**: Uses YOLO model to detect fish in video frames.
- **Tracking**: Tracks detected fish across frames using OpenCV trackers.
- **Annotation**: Allows users to annotate fish behavior by drawing bounding boxes and entering data.
- **GPU Acceleration**: Supports CUDA for faster processing on compatible hardware.
- **Session Management**: Supports resuming from previous sessions.

## Installation

1. **Clone the repository**:
    
    ```sh
    git clone https://github.com/yourusername/WhatFishDo.git
    cd WhatFishDo
    ```

2. **Install dependencies**:
    
    ```sh
    pip install -r requirements.txt
    ```

    **Note for GPU users**: You will need to compile OpenCV with CUDA support. Instructions can be found [here](https://gist.github.com/minhhieutruong0705/8f0ec70c400420e0007c15c98510f133). 

3. **Download YOLO model files**:
    - Download config and weights for a pretrained model of your choosing.
    - Place them in the root directory of the project.
    - Rename them to `model.cfg` and `model.weights` respectively. 
    
    I recommend [YOLO-Fish](https://github.com/tamim662/YOLO-Fish/tree/main) for videos of fish in heterogeneous environments.

## Usage

### Command Line Arguments

- `-g, --gpu`: Run detection model with CUDA.
- `-d, --detect`: Run with detection model.
- `-t, --track`: Run with tracking algorithm.
- `-s, --scale`: Scale the video by factor (default is 2).

### Running the Tool

To run the tool, use the following command:

```sh
python app.py
```

### Key Bindings

- Press `[space]` to pause the video.
- Press `q` to quit the video.
- Press `,` to skip backward.
- Press `.` to skip forward.
- Press `]` to increase speed.
- Press `[` to decrease speed.

### Data and Images

Data and images are saved automatically in the root folder.

### Annotation

Click and drag to draw a bounding box around the fish and start an observation.

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-branch`).
3. Commit your changes (`git commit -am 'Add new feature'`).
4. Push to the branch (`git push origin feature-branch`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [YOLO-Fish](https://github.com/tamim662/YOLO-Fish/tree/main) for the pretrained model.
- [OpenCV](https://opencv.org/) for the computer vision library.