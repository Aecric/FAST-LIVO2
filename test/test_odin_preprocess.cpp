#include "preprocess.h"

#include <gtest/gtest.h>

#include <cstring>

namespace
{
constexpr uint32_t kPointStep = 18;

sensor_msgs::msg::PointField field(const std::string &name, uint32_t offset, uint8_t datatype)
{
  sensor_msgs::msg::PointField result;
  result.name = name;
  result.offset = offset;
  result.datatype = datatype;
  result.count = 1;
  return result;
}

void write_float(std::vector<uint8_t> &data, size_t offset, float value)
{
  std::memcpy(data.data() + offset, &value, sizeof(value));
}

void write_point(sensor_msgs::msg::PointCloud2 &msg, size_t index, float x, float y, float z,
                 uint8_t intensity, uint8_t confidence, float offset_time)
{
  const size_t base = index * kPointStep;
  write_float(msg.data, base + 0, x);
  write_float(msg.data, base + 4, y);
  write_float(msg.data, base + 8, z);
  msg.data[base + 12] = intensity;
  msg.data[base + 13] = confidence;
  // Intentionally unaligned, matching odin_ros_driver2.
  write_float(msg.data, base + 14, offset_time);
}
} // namespace

TEST(OdinPreprocess, ParsesPackedLayoutAndConvertsSecondsToMilliseconds)
{
  using PointField = sensor_msgs::msg::PointField;
  auto msg = std::make_shared<sensor_msgs::msg::PointCloud2>();
  msg->height = 1;
  msg->width = 4;
  msg->is_bigendian = false;
  msg->point_step = kPointStep;
  msg->row_step = msg->width * msg->point_step;
  msg->fields = {
      field("x", 0, PointField::FLOAT32),
      field("y", 4, PointField::FLOAT32),
      field("z", 8, PointField::FLOAT32),
      field("intensity", 12, PointField::UINT8),
      field("confidence", 13, PointField::UINT8),
      field("offset_time", 14, PointField::FLOAT32),
  };
  msg->data.resize(msg->row_step);

  write_point(*msg, 0, 2.0f, 0.0f, 0.0f, 20, 9, 0.012f);
  write_point(*msg, 1, 4.0f, 0.0f, 0.0f, 40, 6, 0.006f); // low confidence
  write_point(*msg, 2, 0.0f, 0.0f, 0.0f, 60, 9, 0.009f); // invalid zero point
  write_point(*msg, 3, 3.0f, 0.0f, 0.0f, 30, 8, 0.003f);

  Preprocess preprocess;
  preprocess.lidar_type = ODIN;
  preprocess.point_filter_num = 1;
  preprocess.odin_confidence_threshold = 7;
  preprocess.blind = 0.2;
  preprocess.blind_sqr = preprocess.blind * preprocess.blind;

  PointCloudXYZI::Ptr output(new PointCloudXYZI());
  preprocess.process(msg, output);

  ASSERT_EQ(output->size(), 2U);
  EXPECT_FLOAT_EQ(output->points[0].x, 3.0f);
  EXPECT_FLOAT_EQ(output->points[0].intensity, 30.0f);
  EXPECT_NEAR(output->points[0].curvature, 3.0f, 1e-5f);
  EXPECT_FLOAT_EQ(output->points[1].x, 2.0f);
  EXPECT_FLOAT_EQ(output->points[1].intensity, 20.0f);
  EXPECT_NEAR(output->points[1].curvature, 12.0f, 1e-5f);
}
