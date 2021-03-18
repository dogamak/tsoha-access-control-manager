<template>
  <div class="editor-root" @mousemove="onMouseMove">
    <svg ref="canvas" id="canvas" @mousedown="onMouseDown" @mouseup="onMouseUp">
      <pattern ref="grid" id="grid" width=50 height=50 patternUnits="userSpaceOnUse">
        <rect width=50 height=50 class="grid-rect" />
      </pattern>
      <rect width="100%" height="100%" fill="url(#grid)" />
      <g ref="zoom_group">
        <line ref="pointer_line" class="pointer-line" :style="{ opacity: previous_point !== null ? 1.0 : 0.0 }" />
        <g class="rooms" ref="rooms"></g>
        <g class="segments" ref="segments"></g>
        <g class="points" ref="points"></g>
        <g class="room_labels" ref="room_labels"></g>
        <g class="debug" ref="debug_vectors"></g>
      </g>
    </svg>
    <FloorSelector />
    <Toolbar :tools="tools" v-model="selectedTool" />
    <div class="absolute right-0 top-0 m-10">
      <div class="rounded-xl bg-white overflow-hidden shadow-xl" style="width: 13em;" v-if="rooms.length > 0">
        <div class="bg-blue-500 font-bold text-white px-5 py-1">Rooms</div>
        <div>
          <div class="px-5 py-1" v-for="(room, i) in rooms">
            <span>{{ room.name }}</span>
          </div>
        </div>
      </div>
    </div>
    <dialogs-wrapper></dialogs-wrapper>
  </div>
</template>

<script>
  import Toolbar from './Toolbar.vue';
  import FloorSelector from './FloorSelector.vue';
  import RoomOptionsDialog from './RoomOptionsDialog.vue';

  import { create as createDialog } from 'vue-modal-dialogs';

  import * as d3 from 'd3';

  const vec = {
    add:    (a, b) => ({ x: a.x + b.x, y: a.y + b.y }),
    sub:    (a, b) => ({ x: a.x - b.x, y: a.y - b.y }),
    mul:    (a, x) => ({ x: a.x * x,   y: a.y * x   }),
    div:    (a, x) => ({ x: a.x / x,   y: a.y / x   }),
    dot:    (a, b) => a.x * b.x + a.y * b.y,
    cross:  (a, b) => a.x * b.y - a.y * b.x,
    unit:      (a) => vec.div(a, vec.magnitude(a)),
    angle:  (a, b) => (2 * Math.PI + Math.atan2(vec.cross(a,b), vec.dot(a,b))) % Math.PI,
    magnitude: (a) => Math.sqrt(Math.pow(a.x, 2) + Math.pow(a.y, 2)),
  };

  const roomOptionsDialog = createDialog(RoomOptionsDialog);

  export default {
    components: { Toolbar, FloorSelector },

    data () {
      let moving_item = null;
      let offset_x;
      let offset_y;

      return {
        points: [],

        segments: [],

        rooms: [],

        previous_point: null,

        hovering: null,

        selectedTool: null,

        debug_vectors: [],

        tools: [
          {
            icon: 'W',
            label: 'Wall Segment',
            mousedown (evt) {
              let transform = d3.zoomTransform(this.$refs.zoom_group);
              let [x, y] = transform.invert(d3.pointer(evt, this.$refs.canvas));

              let end;
              let start = this.previous_point;

              if (this.hovering && this.hovering.type === 'point') {
                if (this.previous_point !== null) {
                  end = this.hovering.index;
                  this.previous_point = null;
                } else {
                  this.previous_point = this.hovering.index;
                }
              } else {
                this.points.push({ x, y });
                this.previous_point = end = this.points.length - 1;
              }

              if (start !== null) {
                this.segments.push({
                  start,
                  end,
                });
              }
            },
          },
          {
            icon: 'M',
            label: 'Move',
            mousedown (evt) {
              moving_item = this.hovering;

              let transform = d3.zoomTransform(this.$refs.zoom_group);
              let [x, y] = transform.invert(d3.pointer(evt, this.$refs.canvas));

              if (moving_item && moving_item.type === 'point') {
                let point = this.points[moving_item.index];

                offset_x = x - point.x;
                offset_y = y - point.y;
              }

              if (moving_item && moving_item.type === 'segment') {
                let segment = this.segments[moving_item.index];
                let point = this.points[segment.start];

                offset_x = x - point.x;
                offset_y = y - point.y;
              }
            },
            mouseup () {
              moving_item = null;
            },
            mousemove (evt) {
              if (moving_item) {
                if (moving_item.type === 'point') {
                  let point = this.points[moving_item.index];
                  let transform = d3.zoomTransform(this.$refs.zoom_group);
                  let [x, y] = transform.invert(d3.pointer(evt, this.$refs.canvas));
                  point.x = x + offset_x;
                  point.y = y + offset_y;

                  let new_points = [ ...this.points ];
                  new_points.splice(moving_item.index, point);
                  this.points = new_points;

                  console.log('Moved! ' + point);
                } else if (moving_item.type === 'segment') {
                  let segment = this.segments[moving_item.index];
                  let start = this.points[segment.start];
                  let end = this.points[segment.end];

                  let transform = d3.zoomTransform(this.$refs.zoom_group);
                  let [x, y] = transform.invert(d3.pointer(evt, this.$refs.canvas));

                  end.x = x - offset_x + (end.x - start.x);
                  end.y = y - offset_y + (end.y - start.y);

                  start.x = x - offset_x;
                  start.y = y - offset_y;

                  let new_points = [ ...this.points ];
                  new_points.splice(segment.start, start);
                  new_points.splice(segment.end, end);
                  this.points = new_points;
                }
              }
            },
          },
          {
            icon: 'R',
            label: 'Room',
            mousedown (evt) {
              let transform = d3.zoomTransform(this.$refs.zoom_group);
              let [x, y] = transform.invert(d3.pointer(evt, this.$refs.canvas));

              let visited = [this.closestSegment(x, y)];

              if (visited[0] === -1)
                return;

              let prev_point = this.segments[visited[0]].start;
              let point = this.segments[visited[0]].end;

              const segmentVec = (s) => {
                let start = this.points[this.segments[s].start];
                let end = this.points[this.segments[s].end];

                return vec.sub(end, start);
              };

              this.debug_vectors.push({
                start: { x, y },
                end: this.points[point],
                color: 'blue',
              });

              let p = this.points[point];
              let pp = this.points[prev_point];

              const cursor_angle = vec.angle(vec.sub(p, { x, y }), vec.sub(p, pp));
              const side = cursor_angle < 0;

              console.log('Cursor angle', cursor_angle);

              while (true) {
                console.log(visited);

                p = this.points[point];
                pp = this.points[prev_point];

                this.debug_vectors.push({
                  start: this.points[prev_point],
                  end: this.points[point],
                  color: 'red',
                });

                let neighbours = this.getPointSegments(point)
                  .map((i) => {
                    let other = this.segments[i].start === point
                      ? this.segments[i].end
                      : this.segments[i].start;

                    let o = this.points[other];

                    console.log(`Point: ${point}, Other: ${other}`);
                    console.log(`Point: ${p.x},${p.y}, Other: ${o.x},${o.y}`);

                    console.log(p, pp, o);
                    let angle = vec.angle(vec.sub(p, o), vec.sub(p, pp));

                    return { i, other, angle };
                  })
                  .filter(({ other }) => other !== prev_point)
                  .sort((a, b) => a.angle - b.angle);

                console.log(neighbours);

                if (neighbours.length === 0)
                  return;

                let tightest = side ? neighbours[0] : neighbours[neighbours.length - 1];

                if (visited.indexOf(tightest.i) !== -1)
                  break;

                prev_point = point;
                point = tightest.other;
                visited.push(tightest.i);
              }

              console.log('Room', visited);

              roomOptionsDialog()
                .then(({ name }) => this.rooms.push({
                  name,
                  segments: visited,
                }));
            },
          },
          {
            icon: 'S',
            label: 'Split',

            mousedown (evt) {
              let transform = d3.zoomTransform(this.$refs.zoom_group);
              let [x, y] = transform.invert(d3.pointer(evt, this.$refs.canvas));

              const { index, point } = this.closestSegmentPoint(x, y);

              if (index === -1)
                return;

              this.points.push(point);

              let tmp = this.segments[index].end;
              this.segments[index].end = this.points.length - 1;

              this.segments.push({
                start: this.points.length - 1,
                end: tmp,
              });
            },
          },
          {
            icon: 'J',
            label: 'Join',

            mousedown () {
              if (!this.hovering || this.hovering.type !== 'point')
                return;

              let point = this.hovering.index;

              let segments = this.segments
                .map((segment, index) => ({ ...segment, index }))
                .filter(s => s.start === point || s.end === point);

              if (segments.length !== 2) {
                return;
              }

              let a = segments[0].start === point ? segments[0].end : segments[0].start;
              let b = segments[1].start === point ? segments[1].end : segments[1].start;

              this.segments[segments[0].index].start = a;
              this.segments[segments[0].index].end = b;

              this.removeSegment(segments[1].index);
            },
          },
        ],
      };
    },

    mounted () {
      d3.select(this.$refs.canvas)
        .call(d3.zoom()
          .extent([[0, 0], [300, 300]])
          .scaleExtent([1, 8])
          .filter((evt) => evt.button === 1)
          .on('zoom', ({ transform }) => {
            d3.select(this.$refs.grid).attr('patternTransform', transform);
            d3.select(this.$refs.zoom_group).attr('transform', transform);
          }));
    },

    watch: {
      points () {
        this.updatePoints();
        this.updateSegments();
        this.updateRooms();
      },

      segments () {
        this.updateSegments();
        this.updateRooms();
      },

      rooms () {
        this.updateRooms();
      },

      debug_vectors () {
        d3.select(this.$refs.debug_vectors).selectAll('line')
          .data(this.debug_vectors)
          .join('line')
          .attr('x1', (d) => d.start.x)
          .attr('y1', (d) => d.start.y)
          .attr('x2', (d) => d.end.x)
          .attr('y2', (d) => d.end.y)
          .attr('stroke', (d) => d.color);

        d3.select(this.$refs.debug_vectors).selectAll('circle')
          .data(this.debug_vectors)
          .join('circle')
          .attr('r', 3)
          .attr('fill', (d) => d.color)
          .attr('cx', (d) => vec.sub(d.end, vec.mul(vec.unit(vec.sub(d.end, d.start)),5)).x)
          .attr('cy', (d) => vec.sub(d.end, vec.mul(vec.unit(vec.sub(d.end, d.start)),5)).y);
      },
    },

    methods: {
      removeSegment (index) {
        for (let i = 0; i < this.rooms.length; i++) {
          const room = this.rooms[i];

          if (room.segments.indexOf(index) !== -1) {
            this.rooms.splice(i, 1);
            i--;
          }

          for (let j = 0; room.segments.length; j++) {
            let segment = room.segments[j];

            if (segment > index) {
              room.segments[j] -= 1;
            }
          }
        }

        this.segments.splice(index, 1);

        const point_references = [];

        for (let i = 0; i < this.points.length; i++)
          point_references[i] = 0;

        for (let { start, end } of this.segments) {
          point_references[start]++;
          point_references[end]++;
        }

        for (let i = 0; i < this.points.length; i++) {
          if (point_references[i] > 0)
            continue;

          // TODO: Remove point.
        }
      },

      getRoomPoints (segments) {
        let usedPoints = [];

        return segments.map(s => {
          let p = this.segments[s].end;

          if (usedPoints.indexOf(p) !== -1) {
            p = this.segments[s].start;
          }

          usedPoints.push(p);

          return p;
        });
      },

      updateRooms () {
        let rooms = d3.select(this.$refs.rooms).selectAll('polygon');

        rooms.data(this.rooms)
          .join('polygon')
          .attr('points', (room) => this.getRoomPoints(room.segments)
              .map(p => this.points[p])
              .map(({x, y}) => [x,y].join(',')).join(' '));

        let room_labels = d3.select(this.$refs.room_labels).selectAll('text');

        room_labels.data(this.rooms)
          .join('text')
          .text((d) => d.name)
          .attr('text-anchor', 'middle')
          .attr('transform', (d) => {
            const polygon = d.segments
              .map(i => this.segments[i])
              .map(s => {
                let { x, y } = this.points[s.end];
                return [x, y];
              });

            console.log(polygon);

            const centroid = d3.polygonCentroid(d3.polygonHull(polygon));

            return `translate(${ centroid })`;
          });
      },

      updatePoints () {
        let circles = d3.select(this.$refs.points).selectAll('circle');

        circles.data(this.points)
          .join('circle')
          .attr('r', 5)
          .attr('cx', (d) => d.x)
          .attr('cy', (d) => d.y)
          .call(this.handleHover('point'));
      },

      updateSegments () {
        let segments = d3.select(this.$refs.segments).selectAll('line');

        segments.data(this.segments)
          .join('line')
          .attr('x1', (d) => this.points[d.start].x)
          .attr('y1', (d) => this.points[d.start].y)
          .attr('x2', (d) => this.points[d.end].x)
          .attr('y2', (d) => this.points[d.end].y)
          .call(this.handleHover('segment'));
      },

      handleHover (type) {
        let local = d3.local();
        let _this = this;

        return (el) => el
          .each(function (d, i) { local.set(this, i); })
          .on('mouseover', function (evt) {
              _this.hovering = { type, index: local.get(this) };
          })
          .on('mouseout', () => this.hovering = null);
      },

      closestSegment (x, y) {
        return this.closestSegmentPoint(x, y).index;
      },

      closestSegmentPoint (x, y) {
        let closest_distance = 0;
        let closest = -1;
        let closest_point = null;
        let i = -1;

        for (const segment of this.segments) {
          i++;

          const start = this.points[segment.start];
          const end = this.points[segment.end];

          const seg_vec = vec.sub(end, start);
          const cur_vec = vec.sub(end, { x, y });

          const projection = vec.dot(seg_vec, cur_vec) / vec.magnitude(seg_vec) / vec.magnitude(seg_vec);

          if (projection < 0 || projection > 1)
            continue;

          const point = vec.sub(end, vec.mul(seg_vec, projection));

          const distance = vec.magnitude(vec.sub({ x, y }, point));

          if (closest === -1 || closest_distance > distance) {
            closest_distance = distance;
            closest_point = point;
            closest = i;
          }
        }

        return {
          index: closest,
          point: closest_point,
        };
      },

      getPointSegments (point) {
        return this.segments
          .map((s, i) => ([s, i]))
          .filter(([s, i]) => s.start === point || s.end === point)
          .map(([s, i]) => i);
      },

      onMouseDown (evt) {
        if (this.selectedTool && this.selectedTool.mousedown) {
          this.selectedTool.mousedown.call(this, evt);
        }
      },

      onMouseUp (evt) {
        if (this.selectedTool && this.selectedTool.mouseup) {
          this.selectedTool.mouseup.call(this, evt);
        }
      },

      onMouseMove (evt) {
        if (this.selectedTool && this.selectedTool.mousemove) {
          this.selectedTool.mousemove.call(this, evt);
        }

        if (this.previous_point !== null) {
          let line = d3.select(this.$refs.pointer_line);

          let transform = d3.zoomTransform(this.$refs.zoom_group);
          let [x, y] = transform.invert(d3.pointer(evt, this.$refs.canvas));

          line
            .attr('x1', this.points[this.previous_point].x)
            .attr('y1', this.points[this.previous_point].y)
            .attr('x2', x)
            .attr('y2', y);
        }
      },
    },
  };
</script>

<style>
  .editor-root {
    position: relative;
    width: 100%;
    height: 100%;
  }

  #canvas {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    width: 100%;
    height: 100%;
  }

  .grid-rect {
    stroke: #ddd;
    stroke-width: 2;
    fill: transparent;
  }

  .points circle:hover {
    stroke: blue;
    stroke-width: 2;
  }

  .pointer-line {
    stroke-width: 3;
    stroke: gray;
    stroke-dasharray: 3 5;
  }

  .segments line {
    stroke-width: 3;
    stroke: black;
  }

  .rooms polygon {
    fill: #60a5fa;
  }

  .dialog {
    position: relative;
    z-index: 1000;
  }
</style>
