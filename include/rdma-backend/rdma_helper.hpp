// MIT License

// Copyright (c) 2022 Duke University. All rights reserved.
// Copyright (c) 2021 ByteDance Inc. All rights reserved.
// Copyright (c) 2021 Duke University.  All rights reserved.

// See LICENSE for license information

#ifndef HELPER_HPP
#define HELPER_HPP
#include <errno.h>
#include <getopt.h>
#include <infiniband/verbs.h>
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <fstream>
#include <iostream>
#include <sstream>
//#include <rdma/rdma_cma.h>
#include <arpa/inet.h>
#include <byteswap.h>
#include <gflags/gflags.h>
#include <glog/logging.h>
#include <netdb.h>
#include <sys/socket.h>
#include <sys/time.h>

#ifdef USE_CUDA
#include </usr/local/cuda/include/cuda.h>
#endif

// For Chelsio Test
DECLARE_bool(cm); 
// 

DECLARE_string(dev);
DECLARE_int32(gid);

DECLARE_bool(server);
DECLARE_string(connect);
DECLARE_int32(port);

DECLARE_int32(min_rnr_timer);
DECLARE_int32(hop_limit);
DECLARE_int32(tos);
DECLARE_int32(qp_timeout);
DECLARE_int32(retry_cnt);
DECLARE_int32(rnr_retry);

DECLARE_int32(qp_type);
DECLARE_int32(mtu);

DECLARE_bool(odp);
DECLARE_int32(thread);
DECLARE_bool(share_cq);
DECLARE_bool(share_mr);
DECLARE_bool(share_pd);
DECLARE_bool(memalign);

DECLARE_int32(send_wq_depth);
DECLARE_int32(recv_wq_depth);
DECLARE_int32(cq_depth);
DECLARE_int32(buf_size);
DECLARE_int32(buf_num);
DECLARE_int32(mr_num);
DECLARE_int32(max_qp_rd_atom);
#ifdef USE_CUDA
DECLARE_bool(use_cuda);
DECLARE_int32(cuda_device_id);
#endif

DECLARE_bool(hw_ts);

// DECLARE_int32(opcode);
// DECLARE_string(opcode_name);

DECLARE_bool(run_infinitely);
DECLARE_int32(iters);

DECLARE_int32(recv_batch);
DECLARE_int32(send_batch);
DECLARE_int32(sge_num);
DECLARE_string(request);
DECLARE_string(receive);
DECLARE_bool(imm_data);

DECLARE_int32(qp_num);
DECLARE_int32(host_num);

DECLARE_bool(print_thp);

DECLARE_bool(inline);
DECLARE_int32(shm_key);

DECLARE_bool(prefetch);

namespace Collie {

constexpr int kUdAddition = 40;
constexpr int kInlineThresh = 64;
constexpr int kHostInfoKey = 0;
constexpr int kMemInfoKey = 1;
constexpr int kChannelInfoKey = 2;
constexpr int kGoGoKey = 3;
constexpr int kCqPollDepth = 128;
constexpr int kMaxBatch = 128;
constexpr int kMaxSge = 16;
constexpr int kMaxInline = 0;
constexpr int kMaxConnRetry = 10;

#if __BYTE_ORDER == __LITTLE_ENDIAN
static inline uint64_t
htonll(uint64_t x) {
    return bswap_64(x);
}

static inline uint64_t
ntohll(uint64_t x) {
    return bswap_64(x);
}
#elif __BYTE_ORDER == __BIG_ENDIAN

static inline uint64_t
htonll(uint64_t x) {
    return x;
}

static inline uint64_t
ntohll(uint64_t x) {
    return x;
}
#else
#error __BYTE_ORDER is neither __LITTLE_ENDIAN nor __BIG_ENDIAN
#endif

class connect_info {
  public:
    int type;
    union {
        struct {
            union ibv_gid gid;
            int number_of_qp;
            int number_of_mem;
        } host;
        struct {
            uint64_t remote_addr;
            uint32_t rkey;
            int size;
        } memory;
        struct {
            int qp_num;  // QP number. For connection setup
            uint16_t dlid;
            uint8_t sl;
        } channel;
    } info;
};
struct ibv_qp_init_attr MakeQpInitAttr(struct ibv_cq *send_cq, struct ibv_cq *recv_cq, int send_wq_depth, int recv_wq_depth);

struct ibv_qp_attr MakeQpAttr(enum ibv_qp_state, enum ibv_qp_type, int remote_qpn, const union ibv_gid &remote_gid, int *attr_mask);

std::vector<std::string> ParseHostlist(const std::string &hostlist);

uint64_t Now64();

uint64_t Now64Ns();

bool ParametersCheck();

int Initialize(int argc, char **argv);
}  // namespace Collie

#endif
