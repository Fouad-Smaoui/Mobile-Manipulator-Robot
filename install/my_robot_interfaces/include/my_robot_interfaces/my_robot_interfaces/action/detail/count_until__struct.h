// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from my_robot_interfaces:action/CountUntil.idl
// generated code does not contain a copyright notice

#ifndef MY_ROBOT_INTERFACES__ACTION__DETAIL__COUNT_UNTIL__STRUCT_H_
#define MY_ROBOT_INTERFACES__ACTION__DETAIL__COUNT_UNTIL__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_Goal
{
  int64_t target_number;
  double period;
} my_robot_interfaces__action__CountUntil_Goal;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_Goal.
typedef struct my_robot_interfaces__action__CountUntil_Goal__Sequence
{
  my_robot_interfaces__action__CountUntil_Goal * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_Goal__Sequence;


// Constants defined in the message

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_Result
{
  int64_t reached_number;
} my_robot_interfaces__action__CountUntil_Result;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_Result.
typedef struct my_robot_interfaces__action__CountUntil_Result__Sequence
{
  my_robot_interfaces__action__CountUntil_Result * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_Result__Sequence;


// Constants defined in the message

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_Feedback
{
  int64_t current_number;
} my_robot_interfaces__action__CountUntil_Feedback;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_Feedback.
typedef struct my_robot_interfaces__action__CountUntil_Feedback__Sequence
{
  my_robot_interfaces__action__CountUntil_Feedback * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_Feedback__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
#include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'goal'
#include "my_robot_interfaces/action/detail/count_until__struct.h"

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_SendGoal_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
  my_robot_interfaces__action__CountUntil_Goal goal;
} my_robot_interfaces__action__CountUntil_SendGoal_Request;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_SendGoal_Request.
typedef struct my_robot_interfaces__action__CountUntil_SendGoal_Request__Sequence
{
  my_robot_interfaces__action__CountUntil_SendGoal_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_SendGoal_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'stamp'
#include "builtin_interfaces/msg/detail/time__struct.h"

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_SendGoal_Response
{
  bool accepted;
  builtin_interfaces__msg__Time stamp;
} my_robot_interfaces__action__CountUntil_SendGoal_Response;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_SendGoal_Response.
typedef struct my_robot_interfaces__action__CountUntil_SendGoal_Response__Sequence
{
  my_robot_interfaces__action__CountUntil_SendGoal_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_SendGoal_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_GetResult_Request
{
  unique_identifier_msgs__msg__UUID goal_id;
} my_robot_interfaces__action__CountUntil_GetResult_Request;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_GetResult_Request.
typedef struct my_robot_interfaces__action__CountUntil_GetResult_Request__Sequence
{
  my_robot_interfaces__action__CountUntil_GetResult_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_GetResult_Request__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'result'
// already included above
// #include "my_robot_interfaces/action/detail/count_until__struct.h"

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_GetResult_Response
{
  int8_t status;
  my_robot_interfaces__action__CountUntil_Result result;
} my_robot_interfaces__action__CountUntil_GetResult_Response;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_GetResult_Response.
typedef struct my_robot_interfaces__action__CountUntil_GetResult_Response__Sequence
{
  my_robot_interfaces__action__CountUntil_GetResult_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_GetResult_Response__Sequence;


// Constants defined in the message

// Include directives for member types
// Member 'goal_id'
// already included above
// #include "unique_identifier_msgs/msg/detail/uuid__struct.h"
// Member 'feedback'
// already included above
// #include "my_robot_interfaces/action/detail/count_until__struct.h"

/// Struct defined in action/CountUntil in the package my_robot_interfaces.
typedef struct my_robot_interfaces__action__CountUntil_FeedbackMessage
{
  unique_identifier_msgs__msg__UUID goal_id;
  my_robot_interfaces__action__CountUntil_Feedback feedback;
} my_robot_interfaces__action__CountUntil_FeedbackMessage;

// Struct for a sequence of my_robot_interfaces__action__CountUntil_FeedbackMessage.
typedef struct my_robot_interfaces__action__CountUntil_FeedbackMessage__Sequence
{
  my_robot_interfaces__action__CountUntil_FeedbackMessage * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} my_robot_interfaces__action__CountUntil_FeedbackMessage__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // MY_ROBOT_INTERFACES__ACTION__DETAIL__COUNT_UNTIL__STRUCT_H_
