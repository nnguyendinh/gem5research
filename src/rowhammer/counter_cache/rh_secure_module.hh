#ifndef __RH_SECURE_MODULE_HH__
#define __RH_SECURE_MODULE_HH__

#include "mem/port.hh"
#include "params/RhSecureModule.hh"
#include "sim/clocked_object.hh"
#include "rowhammer/counter_cache/hardware_queue.hh"

namespace gem5
{

  class RhSecureModule : public ClockedObject
  {
  private:
    // ports
    class CPUSidePort : public ResponsePort
    {
    private:
      /// The object that owns this object (SimpleMemobj)
      RhSecureModule *owner;

      /// True if the port needs to send a retry req.
      // with edits)
      bool needRetry;

      PacketPtr blockedPacket;

    public:
      /**
       * Constructor. Just calls the superclass constructor.
       */
      CPUSidePort(const std::string &name, RhSecureModule *owner)
          : ResponsePort(name), owner(owner), needRetry(false),
            blockedPacket(nullptr) {}

      /**
       * Send a packet across this port. This is called by the owner and
       * all of the flow control is hanled in this function.
       *
       * @param packet to send.
       */
      bool sendPacket(PacketPtr pkt);

      bool sendPacketQueue();

      /**
       * Get a list of the non-overlapping address ranges the owner is
       * responsible for. All response ports must override this function
       * and return a populated list with at least one item.
       *
       * @return a list of ranges responded to
       */
      AddrRangeList getAddrRanges() const override;

    protected:
      /**
       * Receive an atomic request packet from the request port.
       * No need to implement in this simple memobj.
       */
      Tick recvAtomic(PacketPtr pkt) override;

      /**
       * Receive a functional request packet from the request port.
       * Performs a "debug" access updating/reading the data in place.
       *
       * @param packet the requestor sent.
       */
      void recvFunctional(PacketPtr pkt) override;

      /**
       * Receive a timing request from the request port.
       *
       * @param the packet that the requestor sent
       * @return whether this object can consume the packet. If false, we
       *         will call sendRetry() when we can try to receive this
       *         request again.
       */
      bool recvTimingReq(PacketPtr pkt) override;

      /**
       * Called by the request port if sendTimingResp was called on this
       * response port (causing recvTimingResp to be called on the request
       * port) and was unsuccesful.
       */
      void recvRespRetry() override;
    };

    class MemSidePort : public RequestPort
    {
    private:
      /// The object that owns this object (SimpleMemobj)
      RhSecureModule *owner;

      /// If we tried to send a packet and it was blocked, store it here
      PacketPtr blockedPacket;

    public:
      /**
       * Constructor. Just calls the superclass constructor.
       */
      MemSidePort(const std::string &name, RhSecureModule *owner)
          : RequestPort(name), owner(owner), blockedPacket(nullptr) {}

      /**
       * Send a packet across this port. This is called by the owner and
       * all of the flow control is hanled in this function.
       *
       * @param packet to send.
       */
      bool sendPacket(PacketPtr pkt);

      bool sendPacketQueue();

    protected:
      /**
       * Receive a timing response from the response port.
       */
      bool recvTimingResp(PacketPtr pkt) override;

      /**
       * Called by the response port if sendTimingReq was called on this
       * request port (causing recvTimingReq to be called on the responder
       * port) and was unsuccesful.
       */
      void recvReqRetry() override;

      /**
       * Called to receive an address range change from the peer responder
       * port. The default implementation ignores the change and does
       * nothing. Override this function in a derived class if the owner
       * needs to be aware of the address ranges, e.g. in an
       * interconnect component like a bus.
       */
      void recvRangeChange() override;

      // void sendRetryResp() override;
    };

    /**
     * Handle the request from the CPU side
     *
     * @param requesting packet
     * @return true if we can handle the request this cycle, false if the
     *         requestor needs to retry later
     */
    bool
    handleRequest(PacketPtr pkt);

    /**
     * Handle the respone from the memory side
     *
     * @param responding packet
     * @return true if we can handle the response this cycle, false if the
     *         responder needs to retry later
     */
    bool handleResponse(PacketPtr pkt);

    /**
     * Handle a retry from the memory side
     * essentially, just foward the request to the cpu
     * @return true if we can send the retry this cycle, false if we need to
     *        wait
     */

    void handleMemRespRetry();

    /**
     * Handle a retry from the CPU side
     * @return true if we can send the retry this cycle, false if we need to
     *       wait
     */
    void handleCpuReqRetry();

    /**
     * Handle any outstanding requests like a retry from the CPU
     */

    void cleanReady();

    /**
     * Handle a packet functionally. Update the data on a write and get the
     * data on a read.
     *
     * @param packet to functionally handle
     */
    void handleFunctional(PacketPtr pkt);

    void cycle();

    void setPacketReady(bool *b);

    /**
     * Return the address ranges this memobj is responsible for. Just use the
     * same as the next upper level of the hierarchy.
     *
     * @return the address ranges this memobj is responsible for
     */
    AddrRangeList getAddrRanges() const;

    /**
     * Tell the CPU side to ask for our memory ranges.
     */
    void sendRangeChange();

    /// Instantiation of the CPU-side ports
    // std::vector<CPUSidePort> cpuPorts;
    // std::vector<MemSidePort> memPorts;

    int waitingPortId;
    bool waiting = false;

    // ports
    CPUSidePort cpuPort;
    MemSidePort memPort;
    // const Cycles latency;
    const Cycles mem_issue_latency;
    const Cycles read_issue_latency;
    const Cycles write_issue_latency;
    // const Cycles read_verif_tags_cycles;
    // const Cycles write_calc_tags_cycles;
    // const Cycles key_tag_cache_access_latency;
    // const float sm_cache_hitrate;
    // const Tick dram_avg_access_latency;

    /// True if this is currently blocked waiting for a response.
    bool cpuWaiting;
    bool memWaiting;

    // These flags are set when we deny the CPU a request
    // or the memory a response.
    // these flags are crtitical as the program crashes if we try to send
    // a request or response while the other is blocked
    bool cpuBlocked;
    bool memBlocked;

    // These flags are set when we deny the CPU a request
    // or the memory a response.
    bool pendingRequest;
    bool pendingResponse;

    // LimitedQueue<std::tuple<PacketPtr, bool*>> responseQueue;
    LimitedQueue<PacketPtr> responseQueue; // response packets don't need a waiting flag
    LimitedQueue<std::tuple<PacketPtr, bool *>> requestQueue;
    // std::queue<PacketPtr> requestQueue;
    // std::queue<PacketPtr> responseQueue;

    /// If we tried to send a packet and it was blocked, store it here
    // TODO: eventually turn this into a queue
    PacketPtr cpuWaitingPacket;
    // Other RhSecureModule stuff

  protected:
    struct RhSecureModuleStats : public statistics::Group
    {
      RhSecureModuleStats(statistics::Group *parent);
      statistics::Scalar readReqs;
      statistics::Scalar writeReqs;
      // statistics::Scalar hits;
      // statistics::Scalar misses;
      // statistics::Histogram missLatency;
      // statistics::Formula hitRatio;
    } stats;

  public:
    RhSecureModule(const RhSecureModuleParams &p);

    void startup() override;

    /**
     * Get a port with a given name and index. This is used at
     * binding time and returns a reference to a protocol-agnostic
     * port.
     *
     * @param if_name Port name
     * @param idx Index in the case of a VectorPort
     *
     * @return A reference to the given port
     */
    Port &getPort(const std::string &if_name,
                  PortID idx = InvalidPortID) override;
  };

} // namespace gem5

#endif // __SECURE_MODULE_HH__
